Name:           ani-pull
Version:        1.1.0
Release:        1%{?dist}
Summary:        Anime downloader CLI

License:        MIT
URL:            https://github.com/Smasduq/ani-pull
Source0:        %{url}/archive/v%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  python3-setuptools

Requires:       python3-requests
Requires:       python3-beautifulsoup4
Requires:       yt-dlp
Requires:       python3-rich
Requires:       python3-cloudscraper
Requires:       python3-tqdm

%description
A reliable and maintainable anime downloader CLI that searches, selects,
and downloads high-quality anime episodes from Anitaku.to.

%prep
%autosetup -n ani-pull-%{version}

%generate_buildrequires
%pyproject_buildrequires

%build
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files api main

%files -f %{pyproject_files}
%doc README.md
%{_bindir}/ani-pull

%changelog
* Sun May 03 2026 Smasduq <smasduqacc@gmail.com> - 1.1.0-1
- Initial release
