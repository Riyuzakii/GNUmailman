%if 0%{?fedora}
%{!?python3_pkgversion: %global python3_pkgversion 3}
%else
%{!?python3_pkgversion: %global python3_pkgversion 34}
%endif

%global upstream_name mailman-hyperkitty

Name:           mailman3-hyperkitty
Version:        1.0.0
Release:        1%{?dist}
Summary:        Mailman archiver plugin for HyperKitty

License:        GPLv3
URL:            https://gitlab.com/mailman/%{upstream_name}
Source0:        https://pypi.python.org/packages/source/m/%{upstream_name}/%{upstream_name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools
BuildRequires:  python%{python3_pkgversion}-requests
BuildRequires:  python%{python3_pkgversion}-zope-interface
BuildRequires:  mailman3

Requires:       mailman3
Requires:       python%{python3_pkgversion}-setuptools
Requires:       python%{python3_pkgversion}-requests
Requires:       python%{python3_pkgversion}-zope-interface


%description
This package contains a Mailman archiver plugin which sends emails to
HyperKitty, Mailman's web archiver.

All documentation on installing HyperKitty can be found in the documentation
provided by the HyperKitty package. It is also available online at the
following URL: http://hyperkitty.readthedocs.org.


%prep
%setup -q -n %{upstream_name}-%{version}


%build
%{__python3} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python3} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# Mailman config file
install -D -m 644 mailman-hyperkitty.cfg \
    $RPM_BUILD_ROOT%{_sysconfdir}/mailman3.d/hyperkitty.cfg


%check
%{__python3} setup.py test


%files
%doc README.rst LICENSE.txt
%config %{_sysconfdir}/mailman3.d/hyperkitty.cfg
%{python3_sitelib}/*


%changelog
* Wed Apr 29 2015 Aurelien Bompard <abompard@fedoraproject.org> - 1.0.0-1
- version 1.0.0

* Fri Mar 20 2015 Aurelien Bompard <abompard@fedoraproject.org> - 0.3
- initial package
