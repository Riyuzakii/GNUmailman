/*
 * Copyright (C) 2012-2013 by the Free Software Foundation, Inc.
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



function setup_index(url_template) {

    // Setup tooltips
    $('[data-toggle="tooltip"]').tooltip();

    var list_names = [];
    // Collect list names
    $(".all-lists table.lists tr.list").each(function() {
        var listname = $(this).attr("data-list-name");
        if (list_names.indexOf(listname) === -1) {
            list_names.push(listname);
        }
    });

    // Redirect clicks on the whole table row
    $("table.lists tr.list").click(function(e) {
        document.location.href = $(this).find("a.list-name").attr("href");
    });

    // Helper to load the graph
    function show_ajax_chart(listrows) {
        var listname = listrows.first().attr("data-list-name");
        var url = url_template
            .replace(/PLACEHOLDER@PLACEHOLDER/, listname)
            .replace(/PLACEHOLDER%40PLACEHOLDER/, listname);
        return ajax_chart(url, listrows.find("div.chart"), {height: 30});
    }

    // Filter
    function filter_lists() {
        var hide_by_class = {};
        $(".hide-switches input").each(function() {
            var cls = $(this).val();
            hide_by_class[cls] = $(this).prop("checked");
        });
        $("table.lists tr.list").each(function() {
            var must_hide = false;
            // class filter
            for (cls in hide_by_class) {
                if ($(this).hasClass(cls) && hide_by_class[cls]) {
                    must_hide = true;
                }
            }
            // now apply the filters
            if (must_hide) {
                $(this).hide();
            } else {
                $(this).show();
            }
        });
    }
    $(".hide-switches input").click(filter_lists);
    filter_lists(); // Filter on page load

    // Find field
    var find_field = $(".filter-lists input");
    find_field.autocomplete({
        minLength: 3,
        source: "find-list",
        select: function(event, ui) {
            find_field.val(ui.item.value);
            find_field.closest("form").submit();
        },
    });

    // Back to top link
    setup_back_to_top_link(220); // set offset to 220 for link to appear

    // Update list graphs for all lists
    var list_rows = $(".all-lists table.lists tr.list"),
        deferred = $.Deferred();
    deferred.resolve();
    $.each(list_names, function(index, list_name) {
        deferred = deferred.then(function () {
            return show_ajax_chart(list_rows.filter('[data-list-name="' + list_name + '"]'));
        });
    });
}
