================
News / Changelog
================

The Postorius Django app provides a web user interface to
access GNU Mailman.

Postorius is free software: you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, version 3 of the License.

Postorius is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with Postorius. If not, see <http://www.gnu.org/licenses/>.


1.0.3
=====
(2016-02-03)

* Fix security issue


1.0.2
=====
(2015-11-14)

* Bug fix release


1.0.1
=====
(2015-04-28)

* Help texts Small visual alignment fix; removed unnecessary links to
separate help pages.
* Import fix in fieldset_forms module (Django1.6 only)


1.0.0 -- "Frizzle Fry"
======================
(2015-04-17)

* French translation. Provided by Guillaume Libersat
* Addedd an improved test harness using WebTest. Contributed by Aurélien Bompard.
* Show error message in login view. Contributed by Aurélien Bompard (LP: 1094829).
* Fix adding the a list owner on list creation. Contributed by Aurélien Bompard (LP: 1175967).
* Fix untranslatable template strings. Contributed by Sumana Harihareswara (LP: 1157947).
* Fix wrong labels in metrics template. Contributed by Sumana Harihareswara (LP: 1409033).
* URLs now contain the list-id instead of the fqdn_listname. Contributed by Abhilash Raj (LP: 1201150).
* Fix small bug moderator/owner forms on list members page. Contributed by Pranjal Yadav (LP: 1308219).
* Fix broken translation string on the login page. Contributed by Pranjal Yadav.
* Show held message details in a modal window. Contributed by Abhilash Raj (LP: 1004049).
* Rework of internal testing
* Mozilla Persona integration: switch from django-social-auto to django-browserid: Contributed by Abhilash Raj.
* Fix manage.py mmclient command for non-IPython shells. Contributed by Ankush Sharma (LP: 1428169).
* Added archiver options: Site-wide enabled archivers can not be enabled
on a per-list basis through the web UI.
* Added functionality to choose or switch subscription addresses. Contributed by Abhilash Raj.
* Added subscription moderation, pre_verification/_confirmation.
* Several style changes.


1.0 beta 1 -- "Year of the Parrot"
==================================
(2014-04-22)

* fixed pip install (missing MANIFEST) (LP: 1307624). Contributed by Aurélien Bompard
* list owners: edit member preferences
* users: add multiple email addresses
* list info: show only subscribe or unsubscribe button. Contributed by Bhargav Golla
* remove members/owners/moderator. Contributed by Abhilash Raj


1.0 alpha 2 -- "Is It Luck?"
============================
(2014-03-15)

* dev setup fix for Django 1.4 contributed by Rohan Jain
* missing csrf tokens in templates contributed by Richard Wackerbarth (LP: 996658)
* moderation: fixed typo in success message call
* installation documentation for Apache/mod_wsgi
* moved project files to separate branch
* show error message if connection to Mailman API fails
* added list members view
* added developer documentation
* added test helper utils
* all code now conform to PEP8
* themes: removed obsolete MAILMAN_THEME settings from templates, contexts, file structure; contributed by Richard Wackerbarth (LP: 1043258)
* added access control for list owners and moderators
* added a mailmanclient shell to use as a `manage.py` command (`python manage.py mmclient`)
* use "url from future" template tag in all templates. Contributed by Richard Wackerbarth.
* added "new user" form. Contributed by George Chatzisofroniou.
* added user subscription page
* added decorator to allow login via http basic auth (to allow non-browser clients to use API views)
* added api view for list index
* several changes regarding style and navigation structure
* updated to jQuery 1.8. Contributed by Richard Wackerbarth.
* added a favicon. Contributed by Richard Wackerbarth.
* renamed some menu items. Contributed by Richard Wackerbarth.
* changed static file inclusion. Contributed by Richard Wackerbarth.
* added delete domain feature.
* url conf refactoring. Contributed by Richard Wackerbarth.
* added user deletion feature. Contributed by Varun Sharma.



1.0 alpha 1 -- "Space Farm"
===========================
(2012-03-23)

Many thanks go out to Anna Senarclens de Grancy and Benedict Stein for
developing the initial versions of this Django app during the Google Summer of
Code 2010 and 2011.

* add/remove/edit mailing lists
* edit list settings
* show all mailing lists on server
* subscribe/unsubscribe/mass subscribe mailing lists
* add/remove domains
* show basic list info and metrics
* login using django user account or using BrowserID
* show basic user profile
* accept/discard/reject/defer messages
* Implementation of Django Messages contributed by Benedict Stein (LP: #920084)
* Dependency check in setup.py contributed by Daniel Mizyrycki
* Proper processing of acceptable aliases in list settings form contributed by
  Daniel Mizyrycki
