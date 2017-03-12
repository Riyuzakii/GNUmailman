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



function setup_overview(recent_activity_url) {
    function redraw_chart() {
        var element = $(".stats .chart"),
            chartDivWidth = element.width();
        ajax_chart(recent_activity_url, element, {width: chartDivWidth});
    }
    $(window).resize(redraw_chart);
    redraw_chart();

    // Back to top link
    setup_back_to_top_link(220); // set offset to 220 for link to appear

    // submit search on enter (only add if there's a nav-tab's search box)
    if ($('ul.nav-tabs').length > 0) {
        $(document).ready(function() {
            $('#nav-tab-search').keydown(function(e) {
                // if enter is pressed
                if (e.keyCode == 13) {
                    $(this).closest('form').submit();
                    return false;
                 }
            });
        });
    }

    // Collapsible thread lists
    function collapsibleDivs() {
        if (!$(this).next('.list-group').is(':visible')) {
            $(this).children('.fa-caret-right')
                   .removeClass("fa-caret-right")
                   .addClass("fa-caret-down");
            $(this).next('.list-group').slideDown();
        }
        else {
            $(this).next('.list-group').slideUp();
            $(this).children('.fa-caret-down')
                   .removeClass("fa-caret-down")
                   .addClass("fa-caret-right");
        }
    }
    $('#flagged h3').click(collapsibleDivs);
    $('#posted-to h3').click(collapsibleDivs);

    // "More threads" links
    $('.more-threads').click(function(e) {
        e.preventDefault();
        //var more_block = $(this).parent('.more-threads');
        var more_block = $(this).parent().next();
        more_block.children().slice(0, 5)
            .hide().insertBefore($(this)).slideDown();
        if (more_block.children().length === 0) {
            more_block.remove();
            $(this).remove();
        }
    });
}
