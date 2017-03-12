/*
 * Copyright (C) 1998-2012 by the Free Software Foundation, Inc.
 *
 * This file is part of HyperKitty.
 *
 * HyperKitty is free software: you can redistribute it and/or modify it under
 * the terms of the GNU General Public License as published by the Free
 * Software Foundation, either version 3 of the License, or (at your option)
 * any later version.
 *
 * HyperKitty is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along with
 * HyperKitty.  If not, see <http://www.gnu.org/licenses/>.
 *
 * Author: Aurelien Bompard <abompard@fedoraproject.org>
 */


/*
 * Generic
 */
function form_to_json(form) {
    var form_data = form.serializeArray();
    var data = {};
    for (input in form_data) {
        data[form_data[input].name] = form_data[input].value;
    }
    return data;
}



/*
 * Voting
 */

function vote(elem) {
    if ($(elem).hasClass("disabled")) {
        return;
    }
    var value = parseInt($(elem).attr("data-vote"));
    var form = $(elem).parents("form").first();
    var data = form_to_json(form);
    data['vote'] = value;
    $.ajax({
        type: "POST",
        url: form.attr("action"),
        dataType: "json",
        data: data,
        success: function(response) {
            form.replaceWith($(response.html));
        },
        error: function(jqXHR, textStatus, errorThrown) {
            alert(jqXHR.responseText);
        }
    });
}


function setup_vote() {
    $("div.container").on("click", "a.vote", function(e) {
        e.preventDefault();
        vote(this);
    });
}



/*
 * Recent activity bar chart
 */

function chart(elem_id, data, default_props) {
    /* Function for grid lines, for x-axis */
    function make_x_axis() {
    return d3.svg.axis()
        .scale(x)
        .orient("bottom")
        .ticks(d3.time.days, 1)
    }

    /* Function for grid lines, for y-axis */
    function make_y_axis() {
    return d3.svg.axis()
        .scale(y)
        .orient("left")
        .ticks(5)
    }
    if (typeof default_props === "undefined") {
        default_props = {};
    }

    if (!data) { return; }

    var props = {width: 250, height: 50};
    $.extend(props, default_props);
    var margin = {top: 0, right: 0, bottom: 0, left: 0},
        width = props.width - margin.left - margin.right,
        height = props.height - margin.top - margin.bottom;

    var w = Math.floor(width / data.length);

    var format_in = d3.time.format("%Y-%m-%d");
    var format_out = d3.time.format("");

    var x = d3.time.scale()
        .range([0, width]);

    var y = d3.scale.linear()
        .range([height, 0]);

    var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom")
    .tickSize(0,0) // change to 2,2 for ticks
        .tickFormat(format_out)
        .ticks(d3.time.days, 1);

    var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left")
    .tickSize(0,0) // change to 4,3 for ticks
        .ticks("") // change to 2 for y-axis tick labels
        .tickSubdivide(1);

    var area = d3.svg.area()
        .x(function(d) { return x(d.date); })
      //  .y0(height)
        .y(function(d) { return y(d.count); });

    var svg = d3.select(elem_id).append("svg")
    .attr("class", "chart-data")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
      .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // Convert dates if necessary
    data.forEach(function(d) {
        if (typeof d.date === "string") {
            d.date = format_in.parse(d.date);
        }
    });

    x.domain(d3.extent(data, function(d) { return d.date; }));
    y.domain([0, d3.max(data, function(d) { return d.count; })]);


    /* Draw the grid lines, for x-axis */
    svg.append("g")
    .attr("class", "grid")
    .attr("Transform", "translate(0, " + height + ")")
    .call(make_x_axis()
        .tickSize(height, 0, 0)
        .tickFormat("")
    )

    /* Draw the grid lines, for y-axis */
    svg.append("g")
    .attr("class", "grid")
    .call(make_y_axis()
        .tickSize(-width, 0, 0)
        .tickFormat("")
    )

    svg.append("g").attr("class", "bars").selectAll("rect")
        .data(data)
    .enter().append("rect")
        .attr("x", function(d) { return x(d.date); })
        //.attr("y0", height)
        .attr("y", function(d) { return y(d.count); })
        .attr("width", w)
        .attr("height", function(d) { return height - y(d.count); });

    /* draw x-axis */
    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
      . call(xAxis)
      /*.selectAll("text")
        .attr("y", -5)
        .attr("x", -30)
        .attr("transform", function(d) {
            return "rotate(-90)"
            });*/

    /* Y-axis label */
    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
    /*.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", 0)
      .attr("x", 0 - height/2)
      .attr("dy", "-3em")
      .style("text-anchor", "middle")
      .style("fill", "#777")
        .text("Messages"); */
}


function ajax_chart(url, elements, props) {
    elements = $(elements);
    if (elements.data("chart_loading") || elements.find("img.ajaxloader").length == 0) {
        return; // already loaded or being loaded
    }
    elements.data("chart_loading", true);
    // if there's already a chart drawn, remove it and then redraw
    // this would occur when resizing the browser
    if (elements.find("svg.chart-data")) {
        elements.find("svg.chart-data").remove();
    }
    return $.ajax({
        dataType: "json",
        url: url,
        success: function(data) {
            elements.each(function(index, elem) {
                chart($(this).get(0), data.evolution, props);
            });
        },
        error: function(jqXHR, textStatus, errorThrown) {
            //alert(jqXHR.responseText);
        },
        complete: function(jqXHR, textStatus) {
            // if the list is private we have no info, remove the img anyway
            elements.find("img.ajaxloader").remove();
            elements.removeData("chart_loading");
        }
    });
}




/*
 * Misc.
 */

function setup_disabled_tooltips() {
    $("body")
        .tooltip({selector: "a.disabled"})
        .on("click", "a.disabled", function(e) {
            e.preventDefault();
        });
}

function setup_flash_messages() {
    $('.flashmsgs .alert.success').delay(3000).fadeOut('slow');
}

function setup_back_to_top_link(offset, duration) {
    // default scroll to top animation will last 1/4 secs
    duration = (typeof duration !== 'undefined' ? duration : 250);
    $(window).scroll(function() {
        var button = $(".back-to-top");
        if ($(this).scrollTop() > offset && button.is(":hidden")) {
            $(".back-to-top").stop().fadeIn(duration);
        } else if ($(this).scrollTop() <= offset && button.is(":visible")) {
            $(".back-to-top").stop().fadeOut(duration);
        }
    });
    $(".back-to-top").click(function(e) {
        e.preventDefault();
        $("html").animate({scrollTop: 0}, duration);
    })
}

function setup_send_as() {
    $("div.container").on("click", ".send-as-default", function(e) {
        e.preventDefault();
        var select = $(this).next();
        $(this).hide();
        select.show();
    });
}

function setup_expander() {
    $('span.expander').expander({
        slicePoint: 500,
        userCollapseText : '\n[View Less]',
        expandText : '\n[View More]',
        beforeExpand: function() {
            $(this).removeClass("collapsed");
            $(this).addClass("expanded");
        },
        onCollapse: function() {
            $(this).removeClass("expanded");
            $(this).addClass("collapsed");
        }
    });
}


/*
 * Activate
 */

$(document).ready(function() {
    setup_vote();
    setup_disabled_tooltips();
    setup_flash_messages();
    setup_emails_list();
    setup_send_as();
    setup_expander();
});
