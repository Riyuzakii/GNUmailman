/*
 * Copyright (C) 2016 by the Free Software Foundation, Inc.
 *
 * This file is part of Django-Mailman.
 *
 * Django-Mailman is free software: you can redistribute it and/or modify it under
 * the terms of the GNU General Public License as published by the Free
 * Software Foundation, either version 3 of the License, or (at your option)
 * any later version.
 *
 * Django-Mailman is distributed in the hope that it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
 * more details.
 *
 * You should have received a copy of the GNU General Public License along with
 * Django-Mailman.  If not, see <http://www.gnu.org/licenses/>.
 *
 * Author: Aurelien Bompard <abompard@fedoraproject.org>
 */


function setup_paginator() {
    $("body")
        .on("click", "a.jump-to-page", function(e) {
            e.preventDefault();
            $(this).closest(".paginator").find("form.jump-to-page").slideToggle("fast");
        })
        .on("change", ".paginator form select", function() {
            $(this).closest("form").submit();
        })
        .find(".paginator form input[type='submit']").hide();
}


/* Activate */

$(document).ready(function() {
    setup_paginator();
});
