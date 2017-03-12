%global pypi_name HyperKitty
#%%global prerel 1

Name:           hyperkitty
Version:        1.0.4
Release:        %{?prerel:0.}1%{?dist}
Summary:        A web interface to access GNU Mailman v3 archives

License:        GPLv3
URL:            https://gitlab.com/mailman/hyperkitty
Source0:        http://pypi.python.org/packages/source/H/%{pypi_name}/%{pypi_name}-%{version}%{?prerel:dev}.tar.gz

# Patch settings to use the FHS
Patch0:         hyperkitty-fhs.patch

BuildArch:      noarch

BuildRequires:  python-devel
BuildRequires:  python-sphinx
# Unit tests in %%check
BuildRequires:  python-django-gravatar2
BuildRequires:  python-django-rest-framework >= 2.2.0
BuildRequires:  python-django-compressor
BuildRequires:  python-rjsmin
BuildRequires:  sassc
BuildRequires:  python-mailman-client
BuildRequires:  python-robot-detection
BuildRequires:  pytz
BuildRequires:  django-paintstore
BuildRequires:  python-django >= 1.8
BuildRequires:  python-dateutil
BuildRequires:  python-networkx
BuildRequires:  python-enum34
BuildRequires:  python-django-haystack >= 2.5.0
BuildRequires:  python-django-extensions
BuildRequires:  python-django-mailman3
BuildRequires:  python-lockfile
BuildRequires:  python-six
# Unit tests only
BuildRequires:  python-beautifulsoup4
BuildRequires:  python-mock
BuildRequires:  python-whoosh

# SELinux
BuildRequires:  checkpolicy, selinux-policy-devel, /usr/share/selinux/devel/policyhelp
BuildRequires:  hardlink

Requires:       python-django-gravatar2
Requires:       python-django-rest-framework >= 2.2.0
Requires:       python-django-compressor
Requires:       python-rjsmin
Requires:       sassc
Requires:       python-mailman-client
Requires:       python-robot-detection
Requires:       pytz
Requires:       django-paintstore
Requires:       python-django >= 1.8
Requires:       python-dateutil
Requires:       python-networkx
Requires:       python-enum34
Requires:       python-django-haystack >= 2.5.0
Requires:       python-django-extensions
Requires:       python-django-mailman3
Requires:       python-lockfile
Requires:       python-six
Requires:       numpy


%description
HyperKitty is an open source Django application under development. It aims at
providing a web interface to access GNU Mailman archives.
The code is available from: https://gitlab.com/mailman/hyperkitty .
The documentation can be browsed online at https://hyperkitty.readthedocs.org .


%package selinux
%global selinux_variants mls targeted
Summary:        SELinux policy module for %{name}
Requires:       %{name} = %{version}-%{release}
%{!?_selinux_policy_version: %global _selinux_policy_version %(sed -e 's,.*selinux-policy-\\([^/]*\\)/.*,\\1,' /usr/share/selinux/devel/policyhelp 2>/dev/null)}
%if "%{_selinux_policy_version}" != ""
Requires:      selinux-policy >= %{_selinux_policy_version}
%endif

Requires(post):   /usr/sbin/semodule, /sbin/restorecon, /sbin/fixfiles, %{name}
Requires(postun): /usr/sbin/semodule, /sbin/restorecon, /sbin/fixfiles, %{name}

%description selinux
This is the SELinux module for %{name}, install it if you are using SELinux.



%prep
%setup -q -n %{pypi_name}-%{version}%{?prerel:dev}
%patch0 -p0

# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info
# remove shebang on manage.py
sed -i -e '1d' example_project/manage.py
# remove executable permissions on wsgi.py
chmod -x example_project/wsgi.py
# remove __init__.py in example_project to prevent it from being
# installed (find_package won't find it). It's empty anyway.
rm -f example_project/__init__.py

# SELinux
mkdir SELinux
echo '%{_localstatedir}/lib/%{name}/sites(/.*)? gen_context(system_u:object_r:httpd_sys_content_t,s0)' \
    > SELinux/%{name}.fc
# remember to bump the following version if the policy is updated
echo "policy_module(%{name}, 1.0)" > SELinux/%{name}.te


%build
%{__python} setup.py build

# generate html docs
sphinx-build doc html
# remove the sphinx-build leftovers
rm -rf html/.{doctrees,buildinfo}

# SELinux
cd SELinux
for selinuxvariant in %{selinux_variants}; do
  make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile
  mv %{name}.pp %{name}.pp.${selinuxvariant}
  make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile clean
done
cd -


%install
rm -rf %{buildroot}
%{__python} setup.py install --skip-build --root %{buildroot}

# Install the Django files
mkdir -p %{buildroot}%{_sysconfdir}/%{name}/sites/default
cp -p example_project/{manage,settings,urls,wsgi}.py \
    %{buildroot}%{_sysconfdir}/%{name}/sites/default/
touch --reference example_project/manage.py \
    %{buildroot}%{_sysconfdir}/%{name}/sites/default/__init__.py
# Apache HTTPd config file
install -p -m 644 -D example_project/apache.conf \
     %{buildroot}/%{_sysconfdir}/httpd/conf.d/hyperkitty.conf
touch --reference example_project/apache.conf \
    %{buildroot}/%{_sysconfdir}/httpd/conf.d/hyperkitty.conf
# SQLite databases directory, static files and fulltext_index
mkdir -p %{buildroot}%{_localstatedir}/lib/%{name}/sites/default/static
mkdir -p %{buildroot}%{_localstatedir}/lib/%{name}/sites/default/db
mkdir -p %{buildroot}%{_localstatedir}/lib/%{name}/sites/default/fulltext_index
# Cron jobs
mkdir -p %{buildroot}%{_sysconfdir}/cron.d
install -p -m 644 -D example_project/crontab \
    %{buildroot}%{_sysconfdir}/cron.d/%{name}
# Logs
mkdir -p %{buildroot}%{_localstatedir}/log/%{name}/

# SELinux
for selinuxvariant in %{selinux_variants}; do
  install -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
  install -p -m 644 SELinux/%{name}.pp.${selinuxvariant} \
    %{buildroot}%{_datadir}/selinux/${selinuxvariant}/%{name}.pp
done
/usr/sbin/hardlink -cv %{buildroot}%{_datadir}/selinux



%check
PYTHONPATH=`pwd` %{__python} example_project/manage.py test --settings=hyperkitty.tests.settings_test hyperkitty


%post
# Build the static files cache
%{_bindir}/django-admin collectstatic \
    --pythonpath=%{_sysconfdir}/%{name}/sites/default \
    --settings=settings --noinput &>/dev/null || :
%{_bindir}/django-admin compress \
    --pythonpath=%{_sysconfdir}/%{name}/sites/default \
    --settings=settings &>/dev/null || :


%post selinux
for selinuxvariant in %{selinux_variants}; do
  /usr/sbin/semodule -s ${selinuxvariant} -i \
    %{_datadir}/selinux/${selinuxvariant}/%{name}.pp &> /dev/null || :
done
/sbin/fixfiles -R %{name} restore || :
/sbin/restorecon -R %{_localstatedir}/lib/%{name} || :

%postun selinux
if [ $1 -eq 0 ] ; then
  for selinuxvariant in %{selinux_variants}; do
    /usr/sbin/semodule -s ${selinuxvariant} -r %{name} &> /dev/null || :
  done
  /sbin/fixfiles -R %{name} restore || :
  [ -d %{_localstatedir}/lib/%{name} ]  && \
    /sbin/restorecon -R %{_localstatedir}/lib/%{name} &> /dev/null || :
fi


%files
%doc html README.rst COPYING.txt
%config(noreplace) %{_sysconfdir}/%{name}
%config(noreplace) %attr(640,root,apache) %{_sysconfdir}/%{name}/sites/default/settings.py
%config(noreplace) %{_sysconfdir}/httpd/conf.d/%{name}.conf
%config(noreplace) %{_sysconfdir}/cron.d/%{name}
%{python_sitelib}/%{name}
%{python_sitelib}/%{pypi_name}-*.egg-info
%dir %{_localstatedir}/lib/%{name}
%dir %{_localstatedir}/lib/%{name}/sites
%dir %{_localstatedir}/lib/%{name}/sites/default
%dir %{_localstatedir}/lib/%{name}/sites/default/static
%attr(755,apache,apache) %{_localstatedir}/lib/%{name}/sites/default/db
%attr(755,apache,apache) %{_localstatedir}/lib/%{name}/sites/default/fulltext_index
%attr(755,apache,apache) %{_localstatedir}/log/%{name}/

%files selinux
%defattr(-,root,root,0755)
%doc SELinux/*
%{_datadir}/selinux/*/%{name}.pp


%changelog
* Wed Aug 17 2016 Aurelien Bompard <abompard@fedoraproject.org> - 1.0.4-1
- version 1.0.4

* Mon Nov 25 2013 Aurelien Bompard <abompard@fedoraproject.org> - 0.1.7-0.1
- add SELinux policy module, according to:
  http://fedoraproject.org/wiki/SELinux_Policy_Modules_Packaging_Draft

* Thu Aug 15 2013 Aurelien Bompard <abompard@fedoraproject.org> - 0.1.7-0.1
- don't remove the static files cache on uninstall (it may have local
  modifications)

* Tue Jul 23 2013 Aurelien Bompard <abompard@fedoraproject.org> - 0.1.6-1
- version 0.1.6

* Thu Mar 28 2013 Aurelien Bompard <abompard@fedoraproject.org> - 0.1.5-0.2
- put collected static files in _localstatedir

* Tue Feb 19 2013 Aurelien Bompard <abompard@fedoraproject.org> - 0.1.4-1
- update to 0.1.4

* Thu Nov 29 2012 Aurelien Bompard <abompard@fedoraproject.org> - 0.1.3-1
- Initial package.
