%{?_javapackages_macros:%_javapackages_macros}
%{expand: %%global pyver %(python -c 'import sys;print(sys.version[0:3])')}

%global cpython_version    %{pyver}
%global scm_tag            v2.7b3
%global _python_bytecompile_errors_terminate_build 0

Name:                      jython
Version:                   2.7
Release:                   0.2.b3.1
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
# This addresses CVE-2013-2027 (http://bugs.jython.org/msg8004)
Patch2:                    jython-CVE-2013-2027.patch

Requires:                  python >= %{cpython_version}
Requires:                  libreadline-java >= 0.8.0-16
Requires:                  antlr32-java
Requires:                  apache-commons-compress
Requires:                  guava
Requires:                  objectweb-asm
Requires:                  jnr-constants
Requires:                  jnr-ffi
Requires:                  jnr-netdb
Requires:                  jnr-posix
Requires:                  jffi
Requires:                  jline1
Requires:                  icu4j
Requires:                  netty
BuildRequires:             java-devel >= 1:1.7.0
# We build with ant, but install with maven
BuildRequires:             javapackages-local
BuildRequires:             ant
BuildRequires:             junit
BuildRequires:             glassfish-servlet-api
BuildRequires:             python >= %{cpython_version}
BuildRequires:             libreadline-java >= 0.8.0-16
BuildRequires:             antlr32-tool
BuildRequires:             apache-commons-compress
BuildRequires:             guava
BuildRequires:             objectweb-asm
BuildRequires:             jnr-constants
BuildRequires:             jnr-ffi
BuildRequires:             jnr-netdb
BuildRequires:             jnr-posix
BuildRequires:             jffi
BuildRequires:             jline1

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

%description javadoc
API documentation for %{name}.

%package manual
Summary:           Manual for %{name}

%description manual
Usage documentation for %{name}.

%package demo
Summary:           Demo for %{name}
Requires:          %{name} = %{version}-%{release}

%description demo
Demonstrations and samples for %{name}.

%prep
%setup -q -n jython-%{scm_tag}
%patch0
%patch1
%patch2

# Set correct encoding for source
sed -i -e '476i encoding="UTF-8"' -e '715i Encoding="UTF-8"' build.xml

%build
build-jar-repository -s extlibs \
  antlr32/antlr antlr32/antlr-runtime stringtemplate antlr \
  jnr-constants jnr-ffi jnr-netdb jnr-posix jffi \
  libreadline-java/libreadline-java jline1/jline-1 \
  glassfish-servlet-api guava objectweb-asm/asm objectweb-asm/asm-commons objectweb-asm/asm-util \
  commons-compress junit

ant -v \
  -Djython.dev.jar=jython.jar \
  -Dhas.repositories.connection=false \
  developer-build javadoc

# remove shebangs from python files
find dist -type f -name '*.py' | xargs sed -i "s:#!\s*/usr.*::"

pushd maven
# generate maven pom
ant -Dproject.version=%{version} install
popd

# request maven artifact installation
%mvn_artifact build/maven/jython-%{version}.pom dist/jython.jar
%mvn_alias org.python:jython org.python:jython-standalone

%install
# install maven artifacts
%mvn_install -J dist/Doc/javadoc

# data
install -d -m 755 $RPM_BUILD_ROOT%{_datadir}/%{name}
# these are not supposed to be distributed
find dist/Lib -type d -name test | xargs rm -rf
cp -pr dist/Lib $RPM_BUILD_ROOT%{_datadir}/%{name}
# demo
cp -pr Demo $RPM_BUILD_ROOT%{_datadir}/%{name}
# manual
cp -pr Doc $RPM_BUILD_ROOT%{_datadir}/%{name}

# registry
install -m 644 registry $RPM_BUILD_ROOT%{_datadir}/%{name}
# scripts
install -d $RPM_BUILD_ROOT%{_bindir}

cat > $RPM_BUILD_ROOT%{_bindir}/%{name} << EOF
#!/bin/sh

# Source functions library
. %{_datadir}/java-utils/java-functions

# Source system prefs
if [ -f %{_sysconfdir}/%{name}.conf ] ; then
  . %{_sysconfdir}/%{name}.conf
fi

# Source user prefs
if [ -f \$HOME/.%{name}rc ] ; then
  . \$HOME/.%{name}rc
fi

# Arch-specific location of dependency
case \$(uname -m) in
   x86_64 | ia64 | s390x | ppc64 | ppc64le | sparc64 | aarch64 )
      JYTHONLIBDIR="/usr/lib64" ;;
   * )
      JYTHONLIBDIR="/usr/lib" ;;
esac

# Configuration
MAIN_CLASS=org.python.util.jython
BASE_FLAGS=-Dpython.home=%{_datadir}/jython
BASE_JARS="jython/jython guava jnr-constants jnr-ffi jnr-netdb jnr-posix jffi libreadline-java/libreadline-java jline1/jline-1 antlr3-runtime objectweb-asm/asm objectweb-asm/asm-commons objectweb-asm/asm-util commons-compress icu4j netty/netty-buffer netty/netty-codec netty/netty-common netty/netty-handler netty/netty-transport"

BASE_FLAGS="\$BASE_FLAGS -Dpython.console=org.python.util.ReadlineConsole"
BASE_FLAGS="\$BASE_FLAGS -Djava.library.path=\$JYTHONLIBDIR/libreadline-java"
BASE_FLAGS="\$BASE_FLAGS -Dpython.console.readlinelib=Editline"

# Set parameters
set_jvm
set_classpath \$BASE_JARS
set_flags \$BASE_FLAGS
set_options \$BASE_OPTIONS

# Let's start
run "\$@"
EOF

%files -f .mfiles
%doc ACKNOWLEDGMENTS NEWS LICENSE.txt README.txt
%attr(0755,root,root) %{_bindir}/%{name}
%dir %{_datadir}/java/%{name}
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/Lib
%{_datadir}/%{name}/registry

%files javadoc -f .mfiles-javadoc
%doc LICENSE.txt

%files manual
%doc LICENSE.txt
%{_datadir}/%{name}/Doc

%files demo
%doc ACKNOWLEDGMENTS NEWS LICENSE.txt README.txt
%{_datadir}/%{name}/Demo

%changelog
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
