%{?_javapackages_macros:%_javapackages_macros}
%{expand: %%define pyver %(python -c 'import sys;print(sys.version[0:3])')}

%global cpython_version    %{pyver}
%global svn_tag            Release_2_2_1
%global _python_bytecompile_errors_terminate_build 0

Name:                      jython
Version:                   2.2.1
Release:                   14.0%{?dist}
Summary:                   A Java implementation of the Python language
License:                   ASL 1.1 and BSD and CNRI and JPython and Python
URL:                       http://www.jython.org/
# Use the included fetch-jython.sh script to generate the source drop
# for jython 2.2.1
# sh fetch-jython.sh \
#   jython https://jython.svn.sourceforge.net/svnroot Release_2_2_1
#
Source0:                   %{name}-fetched-src-%{svn_tag}.tar.bz2
Source2:                   fetch-%{name}.sh
Patch0:                    %{name}-cachedir.patch
# Make javadoc and copy-full tasks not depend upon "full-build"
# Also, copy python's license from source directory and not
# ${python.home}
Patch1:                    %{name}-nofullbuildpath.patch
Patch2:                    jython-dont-validate-pom.patch
Requires:                  jpackage-utils
Requires:                  jakarta-oro
Requires:                  servlet
Requires:                  python >= %{cpython_version}
Requires:                  libreadline-java >= 0.8.0-16
Requires:                  mysql-connector-java
BuildRequires:             ant
BuildRequires:             libreadline-java >= 0.8.0-16
BuildRequires:             mysql-connector-java
BuildRequires:             jakarta-oro
BuildRequires:             python >= %{cpython_version}
BuildRequires:             servlet
BuildRequires:             java-devel >= 1:1.6.0
BuildRequires:             jpackage-utils
%if 0%{?fedora}
%else
BuildRequires:             ht2html
%endif
Requires:                  java >= 1:1.6.0

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
%setup -q -n %{name}-svn-%{svn_tag}
%patch0 -p1
%patch1 -p1
%patch2 -p1

%build
export CLASSPATH=$(build-classpath mysql-connector-java oro servlet)
# FIXME: fix jpackage-utils to handle multilib correctly
export CLASSPATH=$CLASSPATH:%{_libdir}/libreadline-java/libreadline-java.jar

rm -rf org/apache

perl -p -i -e 's|execon|apply|g' build.xml

ant \
  -Dpython.home=%{_bindir} \
  -Dht2html.dir=%{_datadir}/ht2html \
  -Dpython.lib=./CPythonLib \
  -Dpython.exe=%{_bindir}/python \
  copy-dist


# remove #! from python files
pushd dist
  for f in `find . -name '*.py'`
  do
    sed --in-place  "s:#!\s*/usr.*::" $f
  done
popd

# Create Maven POM's
pushd maven
  ant -Dproject.version=%{version} install
popd

%install
# jar
install -d -m 755 $RPM_BUILD_ROOT%{_javadir}
install -m 644 dist/%{name}.jar \
  $RPM_BUILD_ROOT%{_javadir}/%{name}.jar

# javadoc
install -d -m 755 $RPM_BUILD_ROOT%{_javadocdir}/%{name}
cp -pr dist/Doc/javadoc/* $RPM_BUILD_ROOT%{_javadocdir}/%{name}
# data
install -d -m 755 $RPM_BUILD_ROOT%{_datadir}/%{name}
# these are not supposed to be distributed
find dist/Lib -type d -name test | xargs rm -rf

cp -pr dist/Lib $RPM_BUILD_ROOT%{_datadir}/%{name}
cp -pr dist/Tools $RPM_BUILD_ROOT%{_datadir}/%{name}
# demo
cp -pr dist/Demo $RPM_BUILD_ROOT%{_datadir}/%{name}
# manual
rm -rf dist/Doc/javadoc
mv dist/Doc %{name}-manual-%{version}

# pom
install -d -m 755 $RPM_BUILD_ROOT%{_mavenpomdir}
install -pm 644 build/maven/pom.xml $RPM_BUILD_ROOT%{_mavenpomdir}/JPP-%{name}.pom

# depmap
%add_maven_depmap JPP-%{name}.pom %{name}.jar -a "org.python:jython-standalone"

# registry
install -m 644 registry $RPM_BUILD_ROOT%{_datadir}/%{name}
# scripts
install -d $RPM_BUILD_ROOT%{_bindir}

cat > $RPM_BUILD_ROOT%{_bindir}/%{name} << EOF
#!/bin/sh
#

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
   x86_64 | ia64 | s390x | ppc64 | sparc64 )
      JYTHONLIBDIR="/usr/lib64" ;;
   * )
      JYTHONLIBDIR="/usr/lib" ;;
esac

# Configuration
MAIN_CLASS=org.python.util.%{name}
BASE_FLAGS=-Dpython.home=%{_datadir}/%{name}
BASE_JARS="%{name} oro servlet mysql-connector-java"

BASE_FLAGS="\$BASE_FLAGS -Dpython.console=org.python.util.ReadlineConsole"
BASE_FLAGS="\$BASE_FLAGS -Djava.library.path=\$JYTHONLIBDIR/libreadline-java"
BASE_FLAGS="\$BASE_FLAGS -Dpython.console.readlinelib=Editline"

# Set parameters
set_jvm
CLASSPATH=\$CLASSPATH:\$JYTHONLIBDIR/libreadline-java/libreadline-java.jar
set_classpath \$BASE_JARS
set_flags \$BASE_FLAGS
set_options \$BASE_OPTIONS

# Let's start
run "\$@"
EOF

cat > $RPM_BUILD_ROOT%{_bindir}/%{name}c << EOF
#!/bin/sh
#

%{_bindir}/%{name} %{_datadir}/%{name}/Tools/%{name}c/%{name}c.py "\$@"
EOF

%files
%defattr(-,root,root)
%doc ACKNOWLEDGMENTS NEWS LICENSE.txt README.txt
%attr(0755,root,root) %{_bindir}/%{name}
%attr(0755,root,root) %{_bindir}/%{name}c
%{_javadir}/*
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/Lib
%{_datadir}/%{name}/Tools
%{_datadir}/%{name}/registry
%{_mavenpomdir}/*
%{_mavendepmapfragdir}/*

%files javadoc
%defattr(-,root,root)
%doc LICENSE.txt
%doc %{_javadocdir}/%{name}

%files manual
%defattr(-,root,root)
%doc LICENSE.txt README.txt
%doc %{name}-manual-%{version}

%files demo
%defattr(-,root,root)
%doc ACKNOWLEDGMENTS NEWS LICENSE.txt README.txt
%doc %{_datadir}/%{name}/Demo

%changelog
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
