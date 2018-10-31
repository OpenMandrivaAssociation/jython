%{?_javapackages_macros:%_javapackages_macros}
%global cpython_version    2.7
%global scm_tag            v2.7.1

# Turn off the brp-python-bytecompile script
# We generate JVM bytecode instead
%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$!!g')

Name:                      jython
Version:                   2.7.1
Release:                   3.2
Summary:                   A Java implementation of the Python language
Group:                     Development/Java
License:                   ASL 1.1 and BSD and CNRI and JPython and Python
URL:                       http://www.jython.org/

# Use the included fetch-jython.sh script to generate the source drop
# Usage: sh fetch-jython.sh %%{scm_tag}
Source0:                   jython-%{scm_tag}.tar.xz
Source1:                   fetch-jython.sh

# Make the cache dir be in the user's home
Patch0:                    jython-cachedir.patch
# Avoid rebuilding and validating poms when installing maven stuff and don't gpg sign
Patch1:                    jython-dont-validate-pom.patch
# Dep for this feature is not yet in Fedora
Patch2:                    jython-no-carrotsearch-sizeof.patch
# Tweak launcher script
Patch3:                    jython-launcher.patch
# Fix failure with "import multiprocessing"
Patch4:                    jython-fix-multiprocessing.patch
# Fix tty detection
Patch5:                    jython-fix-tty-detection.patch

Requires:                  python >= %{cpython_version}
Requires:                  antlr32-java
Requires:                  apache-commons-compress
Requires:                  bouncycastle
Requires:                  bouncycastle-pkix
Requires:                  guava
Requires:                  objectweb-asm
Requires:                  jctools >= 2.0.2
Requires:                  jnr-constants
Requires:                  jnr-ffi
Requires:                  jnr-netdb
Requires:                  jnr-posix
Requires:                  jffi
Requires:                  jffi-native
Requires:                  jline
Requires:                  jansi
Requires:                  icu4j
Requires:                  netty >= 4.1.13
Requires:                  xerces-j2
# We build with ant, but install with maven
BuildRequires:             javapackages-local
BuildRequires:             ant
BuildRequires:             ant-junit
BuildRequires:             glassfish-servlet-api
BuildRequires:             python >= %{cpython_version}
BuildRequires:             antlr32-tool
BuildRequires:             apache-commons-compress
BuildRequires:             bouncycastle
BuildRequires:             bouncycastle-pkix
BuildRequires:             guava
BuildRequires:             objectweb-asm
BuildRequires:             jctools >= 2.0.2
BuildRequires:             jnr-constants
BuildRequires:             jnr-ffi
BuildRequires:             jnr-netdb
BuildRequires:             jnr-posix
BuildRequires:             jffi
BuildRequires:             jffi-native
BuildRequires:             jline
BuildRequires:             jansi
BuildRequires:             icu4j
BuildRequires:             netty >= 4.1.13
BuildRequires:             xerces-j2

BuildArch:                 noarch

%description
Jython is an implementation of the high-level, dynamic, object-oriented
language Python seamlessly integrated with the Java platform. The
predecessor to Jython, JPython, is certified as 100% Pure Java. Jython is
freely available for both commercial and non-commercial use and is
distributed with source code. Jython is complementary to Java and is
especially suited for the following tasks: Embedded scripting - Java
programmers can add the Jython libraries to their system to allow end
users to write simple or complicated scripts that add functionality to the
application. Interactive experimentation - Jython provides an interactive
interpreter that can be used to interact with Java packages or with
running Java applications. This allows programmers to experiment and debug
any Java system using Jython. Rapid application development - Python
programs are typically 2-10X shorter than the equivalent Java program.
This translates directly to increased programmer productivity. The
seamless interaction between Python and Java allows developers to freely
mix the two languages both during development and in shipping products.

%package javadoc
Summary:           Javadoc for %{name}
# Obsoletes/Provides added in F25
Obsoletes:         %{name}-manual = %{version}-%{release}
Provides:          %{name}-manual < %{version}-%{release}

%description javadoc
API documentation for %{name}.

%package demo
Summary:           Demo for %{name}
Requires:          %{name} = %{version}-%{release}

%description demo
Demonstrations and samples for %{name}.

%prep
%setup -q -n jython-%{scm_tag}
%patch2 -R -p1
%patch0
%patch1
%patch3
%patch4 -p1
%patch5

rm -rf extlibs/*

# Disable doclint to fix javadoc generation
sed -i -e '/<javadoc/a additionalparam="-Xdoclint:none"' build.xml

# Broader guava compatibility
sed -i -e 's/CharMatcher\.ascii()/CharMatcher.ASCII/' \
  src/org/python/core/PyUnicode.java \
  src/org/python/core/PyBaseCode.java \
  src/org/python/core/Py.java

%build
# Symlink build-time libs
build-jar-repository -p -s extlibs \
  antlr32/antlr antlr32/antlr-runtime stringtemplate antlr \
  jffi jffi-native jnr-constants jnr-ffi jnr-netdb jnr-posix jline/jline jansi/jansi icu4j/icu4j \
  glassfish-servlet-api guava objectweb-asm/asm objectweb-asm/asm-commons objectweb-asm/asm-util \
  commons-compress junit hamcrest/core

ant \
  -Djython.dev.jar=jython.jar \
  -Dhas.repositories.connection=false \
  javatest javadoc

# remove shebangs from python files
find dist -type f -name '*.py' | xargs sed -i "s:#!\s*/usr.*::"

pushd maven
# generate maven pom
ant -Dproject.version=%{version} install
popd

# Symlink run-time libs
rm dist/javalib/*.jar
build-jar-repository -p -s dist/javalib antlr32/antlr-runtime-3.2 \
  objectweb-asm/asm objectweb-asm/asm-commons objectweb-asm/asm-util guava icu4j/icu4j \
  jffi jffi-native jnr-constants jnr-ffi jnr-netdb jnr-posix jline/jline jansi/jansi \
  netty/netty-buffer netty/netty-codec netty/netty-common netty/netty-handler netty/netty-resolver netty/netty-transport \
  jctools/jctools-core apache-commons-compress bcprov bcpkix xerces-j2

# request maven artifact installation
%mvn_artifact build/maven/jython-%{version}.pom dist/jython.jar
%mvn_alias org.python:jython org.python:jython-standalone

%install
# install maven artifacts
%mvn_install -J dist/Doc/javadoc

# jython home dir
install -d -m 755 $RPM_BUILD_ROOT%{_datadir}/%{name}
ln -s %{_javadir}/%{name}/jython.jar $RPM_BUILD_ROOT%{_datadir}/%{name}
cp -pr dist/javalib $RPM_BUILD_ROOT%{_datadir}/%{name}
rm dist/bin/jython_regrtest.bat
cp -pr dist/bin $RPM_BUILD_ROOT%{_datadir}/%{name}
install -m 644 dist/registry $RPM_BUILD_ROOT%{_datadir}/%{name}
# libs without tests
rm -rf dist/Lib/{distutils/tests,email/test,json/tests,test,unittest/test}
cp -pr dist/Lib $RPM_BUILD_ROOT%{_datadir}/%{name}
# demo
cp -pr Demo $RPM_BUILD_ROOT%{_datadir}/%{name}
# javadoc
install -d -m 755 $RPM_BUILD_ROOT%{_datadir}/%{name}/Doc
ln -s %{_javadocdir}/%{name} $RPM_BUILD_ROOT%{_datadir}/%{name}/Doc/javadoc

# scripts
install -d $RPM_BUILD_ROOT%{_bindir}
ln -s %{_datadir}/%{name}/bin/jython $RPM_BUILD_ROOT%{_bindir}

%files -f .mfiles
%doc ACKNOWLEDGMENTS NEWS README.txt
%doc LICENSE.txt
%attr(0755,root,root) %{_bindir}/%{name}
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/bin
%{_datadir}/%{name}/javalib
%{_datadir}/%{name}/jython.jar
%{_datadir}/%{name}/Lib
%{_datadir}/%{name}/registry

%files javadoc -f .mfiles-javadoc
%doc LICENSE.txt
%{_datadir}/%{name}/Doc

%files demo
%doc LICENSE.txt
%{_datadir}/%{name}/Demo

%changelog
* Thu Sep 28 2017 Mat Booth <mat.booth@redhat.com> - 2.7.1-3
- Add missing dep on xerces-j2

* Mon Aug 14 2017 Mat Booth <mat.booth@redhat.com> - 2.7.1-2
- Add missing runtime dep on commons-compress and bouncycastle
- Stricter deps on netty and jctools

* Fri Aug 11 2017 Mat Booth <mat.booth@redhat.com> - 2.7.1-1
- Update to final release of 2.7.1
- Fix tty detection, rhbz#1373279

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.7.1-0.4.b3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2.7.1-0.3.b3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Thu Jan 26 2017 Mat Booth <mat.booth@redhat.com> - 2.7.1-0.2.b3
- Use upstream's launcher script and provide a more complete jython_home directory
  to allow virtualenv to work with jython, rhbz#1373279
- Also enable unit test suite

* Mon Jun 27 2016 Mat Booth <mat.booth@redhat.com> - 2.7.1-0.1.b3
- Update to Jython 2.7.1 to get Jython version of lib2to3

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 2.7-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.7-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Wed May 13 2015 Mat Booth <mat.booth@redhat.com> - 2.7-1
- Update to final release of jython 2.7.0

* Tue Apr 21 2015 Mat Booth <mat.booth@redhat.com> - 2.7-0.8.rc3
- Update to release candidate 3
- Drop upstreamed patch for CVE-2013-1752

* Mon Apr 13 2015 Mat Booth <mat.booth@redhat.com> - 2.7-0.7.rc2
- Fix CVE-2013-1752 - multiple unbound readline() DoS flaws in python stdlib

* Thu Apr 09 2015 Mat Booth <mat.booth@redhat.com> - 2.7-0.6.rc2
- BR/R jnr-posix >= 3.0.9

* Thu Apr 09 2015 Mat Booth <mat.booth@redhat.com> - 2.7-0.5.rc2
- Add hamcrest core to build class path

* Wed Apr 08 2015 Mat Booth <mat.booth@redhat.com> - 2.7-0.4.rc2
- Update to release candidate 2
- Drop jline and libreadline in favour of jline 2
- Resolves: rhbz#1182482 - don't ship windows executables

* Fri Jan 9 2015 Alexander Kurtakov <akurtako@redhat.com> 2.7-0.3.b4
- Update to beta 4.

* Mon Nov 03 2014 Mat Booth <mat.booth@redhat.com> - 2.7-0.2.b3
- Add missing runtime requirements on icu4j and netty
- Fixes: rhbz#1158890

* Thu Jul 31 2014 Mat Booth <mat.booth@redhat.com> - 2.7-0.1.b3
- Update to latest upstream release
- Drop no longer needed patches
- Add aarch64 support to launcher script

* Sun Jun 08 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.5.3-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Mon Jun 02 2014 Mat Booth <mat.booth@redhat.com> - 2.5.3-3
- Fix BRs for mvn_install macro usage

* Mon Jun 02 2014 Mat Booth <mat.booth@redhat.com> - 2.5.3-2
- Port to objectweb-asm 5

* Wed May 28 2014 Mat Booth <mat.booth@redhat.com> - 2.5.3-1
- Updated to latest stable upstream release 2.5.3
- Backported patches for guava and jnr support
- Updated for latest maven packaging guidelines
- Fixed BR/Rs for updates to dependencies

* Thu Mar 6 2014 Alexander Kurtakov <akurtako@redhat.com> 2.2.1-16
- Fix fetch script.
- R java-headless.

* Thu Mar 06 2014 Lubomir Rintel (GoodData) <lubo.rintel@gooddata.com> 2.2.1-15
- Fix CVE-2013-2027

* Mon Aug 12 2013 akurtakov <akurtakov@localhost.localdomain> 2.2.1-14
- PyXML is dead - bug#992651 .

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.2.1-13
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.2.1-12
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Fri Nov 30 2012 Tomas Radej <tradej@redhat.com> - 2.2.1-11
- Removed BR on ht2html

* Thu Jul 19 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.2.1-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue Jun 19 2012 Marek Goldmann <mgoldman@redhat.com> - 2.2.1-9
- Added Maven depmap

* Fri Jan 13 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.2.1-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Mon Jun 6 2011 Alexander Kurtakov <akurtako@redhat.com> 2.2.1-7
- Fix jython script to properly handle classpath.

* Fri Feb 25 2011 Alexander Kurtakov <akurtako@redhat.com> 2.2.1-6
- Fix oro BR/R.
- Remove parts not needed.

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.2.1-5.7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Wed Aug 11 2010 Andrew Overholt <overholt@redhat.com> 2.2.1-4.7
- Rebuild with Python 2.7.

* Mon Jul 12 2010 Andrew Overholt <overholt@redhat.com> 2.2.1-4.6
- Ensure license is also in -javadoc package

* Tue Jun 08 2010 Andrew Overholt <overholt@redhat.com> 2.2.1-4.5
- Fix wrapper script to not reference %%{_libdir} of build machine.
- Resolves bug #601766.

* Tue Feb 16 2010 Andrew Overholt <overholt@redhat.com> 2.2.1-4.4
- Disable _python_bytecompile_errors_terminate_build.
- Disable gcj support.
- Change defines to globals.
- Make noarch.

* Fri Jan 08 2010 Andrew Overholt <overholt@redhat.com> 2.2.1-4.3
- Really fix license.

* Fri Jan 08 2010 Andrew Overholt <overholt@redhat.com> 2.2.1-4.2
- Fix license.
- Fix spaces vs. tabs issue.

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.2.1-4.2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.2.1-3.2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Thu Dec 18 2008 Andrew Overholt <overholt@redhat.com> 2.2.1-2.2
- Rebuild

* Mon Dec 01 2008 Ignacio Vazquez-Abrams <ivazqueznet+rpm@gmail.com> - 2.2.1-2.1
- Rebuild for Python 2.6

* Thu Jul 31 2008 Andrew Overholt <overholt@redhat.com> 2.2.1-1.1
- Fix version since we're on 2.2.1 final

* Wed Jul  9 2008 Tom "spot" Callaway <tcallawa@redhat.com> - 2.2.1-0.1.Release_2_2_1.1.2
- drop repotag

* Tue Mar 18 2008 John Matthews <jmatthew@redhat.com> - 2.2.1-0.1.Release_2_2_1.1jpp.1
- Update to 2.2.1
- Resolves: rhbz#426373

* Tue Feb 19 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 2.2-0.4.Release_2_2beta1.1jpp.3
- Autorebuild for GCC 4.3

* Mon Mar 26 2007 Thomas Fitzsimmons <fitzsim@redhat.com> - 2.2-0.3.Release_2_2beta1.1jpp.3
- Rename doc subpackage "manual".
- Require libreadline-java.
- Correct python.home property value.
- Resolves: rhbz#233949

* Fri Mar 23 2007 Thomas Fitzsimmons <fitzsim@redhat.com> - 2.2-0.3.Release_2_2beta1.1jpp.2
- Fix -Dpython.console.readlinelib=Editline typo.
- Fix LICENSE.txt location in jython-nofullbuildpath.patch.
- Require libreadline-java-devel.
- Check for libJavaEditline.so explicitly in wrapper script.

* Wed Feb 28 2007 Andrew Overholt <overholt@redhat.com> 2.2-0.3.Release_2_2beta1.1jpp.1
- 2.2beta1
- Use 0.z.tag.Xjpp.Y release format
- Remove unnecessary copy of python 2.2 library

* Thu Jan 11 2007 Andrew Overholt <overholt@redhat.com> 2.2-0.2.a1
- Add doc target to nofullbuild patch to actually generate ht2html docs.
- Add doc sub-package.
- Require libreadline-java and mysql-connector-java.

* Tue Dec 19 2006 Andrew Overholt <overholt@redhat.com> 2.2-0.1.a1
- Remove jpp from the release tag.

* Thu Nov 16 2006 Andrew Overholt <overholt@redhat.com> 2.2-0.a1.1jpp_1fc
- Update to 2.2alpha1.
- Include script to generate source tarball.
- Add patch to make javadoc and copy-full tasks not depend upon "full-build".
- Remove manual sub-package as its contents appear to no longer be present.
- Move demo aot-compiled bits to demo package.
- Add rebuild-gcj-db %%post{,un} to demo package.

* Fri Sep 22 2006 Igor Foox <ifoox@redhat.com> 2.2-0.a0.2jpp_5fc
- Remove redundant patch1.

* Thu Sep 21 2006 Igor Foox <ifoox@redhat.com> 2.2-0.a0.2jpp_4fc
- Go back to using the pre-supplied python2.2 source.
- Remove hash-bang from .py files since they are not executable.

* Sat Sep 9 2006 Igor Foox <ifoox@redhat.com> 2.2-0.a0.2jpp_3fc
- Fix Group tags to Development/Languages and Documentation.
- Remove epoch from the jython-demo subpackage's Requires on jython.
- Fix indentation to space-only.
- Added %%doc to files in the -javadoc and -demo packages.

* Fri Sep 8 2006 Igor Foox <ifoox@redhat.com> 2.2-0.a0.2jpp_2fc
- Add dist tag.
- Fix compile line to use the system Python libraries instead of the python2.2
source.
- Remove Source1 (python2.2 library).
- Remove 0 Epoch.
- Remove unneeded 0 Epoch from BRs and Requires.
- Remove Vendor and Distribution tags.
- Fix summary.
- Fix Group, removing Java.
- Change buildroot to standard buildroot.
- Move buildroot removal from prep to install.
- Use libedit (EditLine) instead of GNU readline.

* Thu Jun 1 2006 Igor Foox <ifoox@redhat.com> 0:2.2-0.a0.2jpp_1fc
- Rebuild with ant-1.6.5
- Natively compile
- Add -Dtargetver=1.3
- Changed BuildRoot to what Extras expects

* Mon Aug 23 2004 Randy Watler <rwatler at finali.com> - 0:2.2-0.a0.2jpp
- Rebuild with ant-1.6.2
- Allow build use of python >= 2.3 to generate docs since 2.2 libraries included

* Sun Feb 15 2004 David Walluck <david@anti-microsoft.org> 0:2.2-0.a0.1jpp
- 2.2a0 (CVS)
- add URL tag
- add Distribution tag
- change cachedir patch to use ~/.jython instead of ~/tmp
- remove sys.platform patch
- use included python 2.2 files
- mysql support is back

* Fri Apr 11 2003 David Walluck <david@anti-microsoft.org> 0:2.1-5jpp
- rebuild for JPackage 1.5
- remove mm.mysql support

* Sun Jan 26 2003 David Walluck <david@anti-microsoft.org> 2.1-4jpp
- add PyXML modules from 0.8.2
- make BuildRequires a bit more strict

* Wed Jan 22 2003 David Walluck <david@anti-microsoft.org> 2.1-3jpp
- CVS 20030122
- remove javacc dependency (it's non-free, not needed, and the build is broken)
- add python modules (BuildRequires: python)
- add PyXML modules (BuildRequires: PyXML)
- add HTML documentation (BuildRequires: ht2html)
- optional JavaReadline support (BuildRequires: libreadline-java)
- optional MySQL support (BuildRequires: mm.mysql)
- optional PostgreSQL support is not available at this time due to strange jars
- add jython script
- add jythonc script
- add registry
- Patch0: fix cachedir creation in cwd
- Patch1: fix sys.platform (site.py expects format: <os.name>-<os.arch>)
- remove oro class files from jython and require the oro RPM instead
- change Url tag

* Mon Mar 18 2002 Guillaume Rousse <guillomovitch@users.sourceforge.net> 2.1-2jpp 
- generic servlet support

* Wed Mar 06 2002 Guillaume Rousse <guillomovitch@users.sourceforge.net> 2.1-1jpp 
- 2.1
- section macro

* Thu Jan 17 2002 Guillaume Rousse <guillomovitch@users.sourceforge.net> 2.0-2jpp
- versioned dir for javadoc
- no dependencies for manual and javadoc packages
- stricter dependency for demo package

* Tue Dec 18 2001 Guillaume Rousse <guillomovitch@users.sourceforge.net> 2.0-1jpp
- first JPackage release
