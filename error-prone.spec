Name:		error-prone
Version:	2.50.0
Release:	1
Summary:	Bug pattern annotation for Error Prone checks
Group:		Development/Java
License:	Apache-2.0
URL:		https://errorprone.info/
# Tag v2.50.0. No prebuilt jars or class files. This build ships
# error_prone_annotation only. check_api and core need dataflow-errorprone
# and protobuf-java, which are not packaged yet.
Source0:	https://github.com/google/error-prone/archive/refs/tags/v%{version}.tar.gz#/error-prone-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
BuildRequires:	mvn(com.google.guava:guava)

%description
@BugPattern and its validator from Error Prone %{version}. Error Prone
checks and the core compiler plugin are not in this build.

%prep
%autosetup -n error-prone-%{version}
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete

%build
set -eo pipefail
find annotation/src/main/java -name '*.java' > sources.list
test "$(wc -l < sources.list)" -eq 3
mkdir -p classes
javac --release 21 -encoding UTF-8 -cp %{_javadir}/guava.jar -d classes @sources.list
cat > manifest.mf << 'EOF'
Manifest-Version: 1.0
Automatic-Module-Name: com.google.errorprone.annotation

EOF
jar cfm error_prone_annotation.jar manifest.mf -C classes .
jar i error_prone_annotation.jar
javap -verbose -cp error_prone_annotation.jar com.google.errorprone.BugPatternValidator | grep -F 'major version: 65'
jar --describe-module --file error_prone_annotation.jar > describe.txt
if grep -F -q 'Unable to derive' describe.txt; then
	cat describe.txt
	exit 1
fi

cat > error_prone_annotation.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.google.errorprone</groupId>
  <artifactId>error_prone_annotation</artifactId>
  <version>2.50.0</version>
  <name>Error Prone bug pattern annotation</name>
  <description>@BugPattern annotation used by Error Prone checks</description>
  <url>https://errorprone.info/</url>
  <licenses>
    <license>
      <name>Apache License, Version 2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>com.google.guava</groupId>
      <artifactId>guava</artifactId>
      <version>33.6.0-jre</version>
    </dependency>
  </dependencies>
</project>
EOF

%install
sysjar install --buildroot %{buildroot} \
	--artifact error_prone_annotation.pom:error_prone_annotation.jar \
	--file-name error_prone_annotation \
	--filelist .mfiles

%check
set -eo pipefail
JAR=%{buildroot}%{_javadir}/error_prone_annotation.jar
test -f "$JAR"
mkdir -p check
cat > check/Check.java << 'EOF'
import com.google.errorprone.BugPattern;
import com.google.errorprone.BugPattern.LinkType;
import com.google.errorprone.BugPattern.SeverityLevel;
import com.google.errorprone.BugPatternValidator;
@BugPattern(name = "GradleCheck", summary = "gradle", severity = SeverityLevel.ERROR, linkType = LinkType.NONE)
class Sample {}
public class Check {
	public static void main(String[] args) throws Exception {
		BugPattern pattern = Sample.class.getAnnotation(BugPattern.class);
		BugPatternValidator.validate(pattern);
		System.out.println("epann_ok " + pattern.name() + " " + pattern.summary());
	}
}
EOF
CP="$JAR:%{_javadir}/guava.jar"
javac --release 21 -encoding UTF-8 -cp "$CP" -d check check/Check.java
java -cp "check:$CP" Check > check/check.log
cat check/check.log
grep -F -q 'epann_ok GradleCheck gradle' check/check.log

%files -f .mfiles
%license COPYING
%doc README.md
