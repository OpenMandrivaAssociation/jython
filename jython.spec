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

%define cpython_version	%{py_ver}
%define	pyxml_version	0.8.4
%define	section		free

Name:		jython
Version:	2.2.1
Release:	1
Summary:	Java source interpreter
License:	Modified CNRI Open Source License
URL:		http://www.jython.org/
# svn export https://jython.svn.sourceforge.net/svnroot/jython/tags/Release_2_2_1/jython jython-2.2
Source0:	%{name}-%{version}.tar.bz2
Patch0:		%{name}-cachedir.patch
Patch1:		%{name}-no-copy-python.patch
Patch2:		%{name}-nofullbuildpath.patch
Requires:	jline
Requires:	jpackage-utils >= 0:1.6
Requires:	jakarta-oro
Requires:	libreadline-java
Requires:	servlet
BuildRequires:	java-rpmbuild
BuildRequires:	ant >= 0:1.6
BuildRequires:	ht2html
BuildRequires:	jline
BuildRequires:	libreadline-java
#BuildRequires:	mysql-connector-java
BuildRequires:	jakarta-oro
BuildRequires:	javacc
BuildRequires:	python
# FIXME: PyXML now seems to be shipped with jython
# FIXME: Keeping internal PyXML for now
#BuildRequires:	PyXML >= 0:%{pyxml_version}
BuildRequires:	servlet
Group:		Development/Java
#Distribution:	JPackage
#Vendor:	JPackage Project
BuildArch:	noarch
BuildRequires:	java-devel

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

%package	demo
Summary:	Demo for %{name}
Requires:	%{name} = %{EVRD}
Group:		Development/Java

%description	demo
Demonstrations and samples for %{name}.

%prep
%setup -q
%patch0 -p1
%patch1 -p1
%patch2 -p1 -b .nofullbuild~
# remove all binary libs
%{_bindir}/find . -name "*.jar" | %{_bindir}/xargs %{__rm}
# remove all SVN files
#%{_bindir}/find . -type d -name .svn | %{_bindir}/xargs %{__rm} -r

%{__perl} -pi -e 's/execon/apply/g' build.xml
%{__perl} -pi -e 's/ if="full-build"//g' build.xml
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
  -DPyXmlHome=%{_libdir}/python%pyver \
  -Dtargetver=1.3 \
  copy-dist


# remove #! from python files
pushd dist
  for f in `find . -name '*.py'`
  do
    sed --in-place  "s:#!\s*/usr.*::" $f
  done
popd

%install
# jar
install -d -m 755 %{buildroot}%{_javadir}
install -m 644 dist/%{name}.jar \
  %{buildroot}%{_javadir}/%{name}.jar

# data
install -d -m 755 %{buildroot}%{_datadir}/%{name}
# these are not supposed to be distributed

cp -pr dist/Lib %{buildroot}%{_datadir}/%{name}
cp -pr dist/Tools %{buildroot}%{_datadir}/%{name}
# demo
cp -pr dist/Demo %{buildroot}%{_datadir}/%{name}


# registry
install -m 644 registry %{buildroot}%{_datadir}/%{name}
# scripts
install -d %{buildroot}%{_bindir}

cat > %{buildroot}%{_bindir}/%{name} << EOF
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
CLASSPATH=$CLASSPATH:\$JYTHONLIBDIR/libreadline-java/libreadline-java.jar
set_classpath \$BASE_JARS
set_flags \$BASE_FLAGS
set_options \$BASE_OPTIONS

# Let's start
run "\$@"
EOF

cat > %{buildroot}%{_bindir}/%{name}c << EOF
#!/bin/sh
#
# %{name}c script
# JPackage Project (http://jpackage.sourceforge.net)

%{_bindir}/%{name} %{_datadir}/%{name}/Tools/%{name}c/%{name}c.py "\$@"
EOF

%files
%doc ACKNOWLEDGMENTS NEWS LICENSE.txt README.txt
%attr(0755,root,root) %{_bindir}/%{name}
%attr(0755,root,root) %{_bindir}/%{name}c
%{_javadir}/*
%dir %{_datadir}/%{name}
%dir %{_datadir}/%{name}/Lib
%attr(-,root,root) %{_datadir}/%{name}/Lib/*
%{_datadir}/%{name}/Tools
%{_datadir}/%{name}/registry

%files demo
%{_datadir}/%{name}/Demo
