# Copyright (c) 2000-2007, JPackage Project
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the
#    distribution.
# 3. Neither the name of the JPackage Project nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

%define gcj_support 1
%define cpython_version 2.3
%define pyxml_version   0.8.4
%define section         free

Name:           jython
Version:        2.2.1
Release:        %mkrel 0.0.2
Epoch:          0
Summary:        Java source interpreter
License:        Modified CNRI Open Source License
URL:            http://www.jython.org/
# svn export https://jython.svn.sourceforge.net/svnroot/jython/tags/Release_2_2_1/jython jython-2.2
Source0:        %{name}-%{version}.tar.bz2
Patch0:         %{name}-cachedir.patch
Patch1:         %{name}-no-copy-python.patch
Requires:       jline
Requires:       jpackage-utils >= 0:1.6
Requires:       jakarta-oro
Requires:       libreadline-java
Requires:       servlet
BuildRequires:  java-rpmbuild
BuildRequires:  ant >= 0:1.6
BuildRequires:  ht2html
BuildRequires:  jline
BuildRequires:  libreadline-java
#tmp#BuildRequires:  mysql-connector-java
BuildRequires:  jakarta-oro
BuildRequires:  javacc
BuildRequires:  python >= 0:%{cpython_version}
# FIXME: PyXML now seems to be shipped with jython
# FIXME: Keeping internal PyXML for now
#BuildRequires:  PyXML >= 0:%{pyxml_version}
BuildRequires:  servlet
Group:          Development/Java
#Distribution:  JPackage
#Vendor:        JPackage Project
%if ! %{gcj_support}
BuildArch:      noarch
BuildRequires:  java-devel
%endif
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root
%if %{gcj_support}
BuildRequires:    java-gcj-compat-devel
%endif

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

%package manual
Summary:        Manual for %{name}
Group:          Development/Java

%description manual
Documentation for %{name}.

%package javadoc
Summary:        Javadoc for %{name}
Group:          Development/Java

%description javadoc
Javadoc for %{name}.

%package demo
Summary:        Demo for %{name}
Requires:       %{name} = %{epoch}:%{version}-%{release}
Group:          Development/Java

%description demo
Demonstrations and samples for %{name}.

%prep
%setup -q
%patch0 -p1
%patch1 -p1
# remove all binary libs
%{_bindir}/find . -name "*.jar" | %{_bindir}/xargs %{__rm}
# remove all SVN files
#%{_bindir}/find . -type d -name .svn | %{_bindir}/xargs %{__rm} -r

%{__perl} -pi -e 's/execon/apply/g' build.xml
%{__perl} -pi -e 's/ if="full-build"//g' build.xml

%build
export CLASSPATH=$(build-classpath jline libreadline-java oro servlet)
MYSQLJDBC=
MYSQLJDBC=$(build-classpath mysql-connector-java 2>/dev/null) || :
[ -n "$MYSQLJDBC" ] && CLASSPATH=$CLASSPATH:$MYSQLJDBC

pushd src/org/python/parser
%{__perl} -pi -e 's/ unless="parser.regen.notreq"//g' build.xml
%{ant} clean
popd

%{ant} -Dnowarn=true \
       -DPyXmlHome=%{py_platsitedir} \
       -Dpython.exe=%{__python} \
       -Dpython.home=%{py_puresitedir} \
       -Dht2html.dir=%{_datadir}/ht2html \
       -DjavaccHome=%{_datadir}/javacc \
       -Djavacc.jar=%{_javadir}/javacc.jar \
  parser copy-dist

%install
rm -rf $RPM_BUILD_ROOT
# jar
install -d -m 755 $RPM_BUILD_ROOT%{_javadir}
install -m 644 dist/%{name}.jar $RPM_BUILD_ROOT%{_javadir}/%{name}-%{version}.jar
(cd $RPM_BUILD_ROOT%{_javadir} && for jar in *-%{version}*; do ln -sf ${jar} ${jar/-%{version}/}; done)
# manual
rm -f Doc/Makefile
rm -rf Doc/api
# javadoc
install -d -m 755 $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}
cp -a dist/Doc/javadoc/* $RPM_BUILD_ROOT%{_javadocdir}/%{name}-%{version}
ln -s %{name}-%{version} $RPM_BUILD_ROOT%{_javadocdir}/%{name}
# data
install -d -m 755 $RPM_BUILD_ROOT%{_datadir}/%{name}
# these are not supposed to be distributed
find dist/Lib -type d -name test | xargs rm -rf
cp -a dist/Lib $RPM_BUILD_ROOT%{_datadir}/%{name}
cp -a dist/Tools $RPM_BUILD_ROOT%{_datadir}/%{name}
cp -a dist/Demo $RPM_BUILD_ROOT%{_datadir}/%{name}

# registry
install -m 644 registry $RPM_BUILD_ROOT%{_datadir}/%{name}
# scripts
install -d $RPM_BUILD_ROOT%{_bindir}

cat > $RPM_BUILD_ROOT%{_bindir}/%{name} << EOF
#!/bin/sh
#
# %{name} script
# JPackage Project (http://jpackage.sourceforge.net)

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

# Configuration
MAIN_CLASS=org.python.util.%{name}
BASE_FLAGS=-Dpython.home=%{_datadir}/%{name}
BASE_JARS="%{name} jline libreadline-java oro servlet"

if [ -z "\$JYTHON_CONSOLE_READLINELIB" ]; then
    JYTHON_CONSOLE_READLINELIB="jline"
fi

if [ x"\$JYTHON_CONSOLE_READLINELIB" = xjline ]; then
  BASE_FLAGS="\$BASE_FLAGS -Dpython.console=org.python.util.JLineConsole"
elif [ x"\$JYTHON_CONSOLE_READLINELIB" = xeditline -a -x %{_libdir}/libJavaEditline.so ]; then
  BASE_FLAGS="\$BASE_FLAGS -Dpython.console.readlinelib=Editline"
  BASE_FLAGS="\$BASE_FLAGS -Dpython.console=org.python.util.ReadlineConsole"
  BASE_FLAGS="\$BASE_FLAGS -Djava.library.path=%{_libdir}"
  BASE_JARS="\$BASE_JARS libreadline-java"
elif [ x"\$JYTHON_CONSOLE_READLINELIB" = xreadline -a -x %{_libdir}/libJavaReadline.so ]; then
  BASE_FLAGS="\$BASE_FLAGS -Dpython.console.readlinelib=GnuReadline"
  BASE_FLAGS="\$BASE_FLAGS -Dpython.console=org.python.util.ReadlineConsole"
  BASE_FLAGS="\$BASE_FLAGS -Djava.library.path=%{_libdir}"
  BASE_JARS="\$BASE_JARS libreadline-java"
fi

if [ -f %{_javadir}/mysql-connector-java.jar ]; then
  BASE_JARS="\$BASE_JARS mysql-connector-java"
fi

# Set parameters
set_jvm
set_classpath \$BASE_JARS
set_flags \$BASE_FLAGS
set_options \$BASE_OPTIONS

# Let's start
run "\$@"
EOF

cat > $RPM_BUILD_ROOT%{_bindir}/%{name}c << EOF
#!/bin/sh
#
# %{name}c script
# JPackage Project (http://jpackage.sourceforge.net)

%{_bindir}/%{name} %{_datadir}/%{name}/Tools/%{name}c/%{name}c.py "\$@"
EOF

#rm -f $RPM_BUILD_ROOT%{_datadir}/%{name}/Lib/UserDict.py

for i in `%{_bindir}/find %{buildroot}%{_datadir}/%{name}/Lib -name '*.py'`; do
  if %{__grep} '^#!.*python' $i; then
    %{__perl} -pi -e 's|^#!.*/usr/bin/env.*python.*|#!%{__python}|' $i
    %{__perl} -pi -e 's|/usr/local/bin/python|%{__python}|' $i    
    %{__chmod} 0755 $i
  fi
done

%if %{gcj_support}
%{_bindir}/aot-compile-rpm
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%if %{gcj_support}
%post
%{update_gcjdb}

%postun
%{clean_gcjdb}
%endif

%files
%defattr(-,root,root)
%doc ACKNOWLEDGMENTS NEWS LICENSE.txt README.txt
%attr(0755,root,root) %{_bindir}/%{name}
%attr(0755,root,root) %{_bindir}/%{name}c
%{_javadir}/*
%dir %{_datadir}/%{name}
%dir %{_datadir}/%{name}/Lib
%attr(-,root,root) %{_datadir}/%{name}/Lib/*
%{_datadir}/%{name}/Tools
%{_datadir}/%{name}/registry
%if %{gcj_support}
%dir %{_libdir}/gcj/%{name}
%attr(-,root,root) %{_libdir}/gcj/%{name}/*
%endif

%files manual
%defattr(-,root,root)
%doc dist/Doc/*.html dist/Doc/images

%files javadoc
%defattr(-,root,root)
%{_javadocdir}/%{name}-%{version}
%{_javadocdir}/%{name}

%files demo
%defattr(-,root,root)
%{_datadir}/%{name}/Demo
