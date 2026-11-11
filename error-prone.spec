Name:		error-prone
Version:	2.50.0
Release:	2
Summary:	Error Prone annotation, check API, and core
Group:		Development/Java
License:	Apache-2.0
URL:		https://errorprone.info/
# Tag v2.50.0. No prebuilt jars or class files.
# Release 2 adds error_prone_check_api and error_prone_core beside the
# @BugPattern jar from release 1. check_api is retargeted at the unshaded
# cooker dataflow and javacutil jars. The JDK 24 generator is used because
# Types.SignatureGenerator is a non-static inner class on this JDK.
Source0:	https://github.com/google/error-prone/archive/refs/tags/v%{version}.tar.gz#/error-prone-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
BuildRequires:	protobuf-compiler
BuildRequires:	mvn(com.google.guava:guava) = 33.6.0-jre
BuildRequires:	mvn(com.google.guava:failureaccess) = 1.0.3
BuildRequires:	mvn(com.google.errorprone:error_prone_annotations) = 2.50.0
BuildRequires:	mvn(com.google.auto.value:auto-value) = 1.11.1
BuildRequires:	mvn(com.google.auto.value:auto-value-annotations) = 1.11.1
BuildRequires:	mvn(com.google.auto:auto-common) = 1.2.2
BuildRequires:	mvn(com.squareup:javapoet) = 1.13.0
BuildRequires:	mvn(net.ltgt.gradle.incap:incap) = 1.0.0
BuildRequires:	mvn(com.google.escapevelocity:escapevelocity) = 1.1
BuildRequires:	mvn(org.checkerframework:dataflow) = 3.41.0-eisop1
BuildRequires:	mvn(org.checkerframework:javacutil) = 3.41.0-eisop1
BuildRequires:	mvn(org.checkerframework:checker-qual) = 3.41.0-eisop1
BuildRequires:	mvn(org.plumelib:plume-util) = 1.8.1
BuildRequires:	mvn(com.github.ben-manes.caffeine:caffeine) = 3.0.5
BuildRequires:	mvn(io.github.java-diff-utils:java-diff-utils) = 4.12
BuildRequires:	mvn(com.github.kevinstern:software-and-algorithms) = 1.0
BuildRequires:	mvn(com.google.googlejavaformat:google-java-format) = 1.35.0
BuildRequires:	mvn(org.pcollections:pcollections) = 4.0.1
BuildRequires:	mvn(com.google.auto.service:auto-service-annotations) = 1.1.1
BuildRequires:	mvn(com.google.protobuf:protobuf-java) = 4.33.2
BuildRequires:	mvn(javax.inject:javax.inject) = 1.0.5
BuildRequires:	mvn(org.jspecify:jspecify) = 1.0.0
Requires:	mvn(com.google.errorprone:error_prone_annotations) = 2.50.0
Requires:	mvn(com.google.guava:guava) = 33.6.0-jre
Requires:	mvn(org.checkerframework:dataflow) = 3.41.0-eisop1
Requires:	mvn(org.checkerframework:javacutil) = 3.41.0-eisop1
Requires:	mvn(com.github.ben-manes.caffeine:caffeine) = 3.0.5

%description
Error Prone %{version}: the @BugPattern annotation, the check API, and the
core checks. The check API calls org.checkerframework.dataflow and
javacutil. It does not embed the shaded dataflow-errorprone jar. Core loads
its JDK 8 API diff from the proto resource shipped in error_prone_core.

%prep
%autosetup -n error-prone-%{version}
set -eo pipefail
find . -depth \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -exec /bin/rm -rf {} +
/bin/cp -f check_api/src/main/java24/com/google/errorprone/util/ErrorProneSignatureGenerator.java \
	check_api/src/main/java/com/google/errorprone/util/ErrorProneSignatureGenerator.java
find check_api/src/main/java -name '*.java' -print0 | xargs -0 sed -i \
	-e 's/org\.checkerframework\.errorprone\.dataflow/org.checkerframework.dataflow/g' \
	-e 's/org\.checkerframework\.errorprone\.javacutil/org.checkerframework.javacutil/g'
if grep -R -q 'org.checkerframework.errorprone' check_api/src/main/java; then
	grep -R -n 'org.checkerframework.errorprone' check_api/src/main/java
	exit 1
fi

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"

find annotation/src/main/java -name '*.java' > ann.list
test "$(wc -l < ann.list)" -eq 3
mkdir -p classes-ann
javac --release 21 -encoding UTF-8 -cp %{_javadir}/guava.jar -d classes-ann @ann.list
cat > manifest-ann.mf << 'EOF'
Manifest-Version: 1.0
Automatic-Module-Name: com.google.errorprone.annotation

EOF
jar cfm error_prone_annotation.jar manifest-ann.mf -C classes-ann .
jar i error_prone_annotation.jar
javap -verbose -cp error_prone_annotation.jar com.google.errorprone.BugPatternValidator | grep -F 'major version: 65'
jar --describe-module --file error_prone_annotation.jar > describe-ann.txt
if grep -F -q 'Unable to derive' describe-ann.txt; then
	cat describe-ann.txt
	exit 1
fi

cat > error_prone_annotation.pom << EOF
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.google.errorprone</groupId>
  <artifactId>error_prone_annotation</artifactId>
  <version>%{version}</version>
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

find check_api/src/main/java -name '*.java' > check.list
test "$(wc -l < check.list)" -eq 154
mkdir -p classes-api gen-api
AP="$PWD/error_prone_annotation.jar:%{_javadir}/error_prone_annotations-2.50.0.jar:%{_javadir}/jspecify.jar:%{_javadir}/dataflow.jar:%{_javadir}/java-diff-utils.jar:%{_javadir}/auto-value-annotations.jar:%{_javadir}/auto-value.jar:%{_javadir}/auto-common.jar:%{_javadir}/software-and-algorithms.jar:%{_javadir}/caffeine.jar:%{_javadir}/atinject.jar:%{_javadir}/guava.jar:%{_javadir}/failureaccess.jar:%{_javadir}/checker-qual-3.41.0-eisop1.jar:%{_javadir}/javacutil.jar:%{_javadir}/plume-util.jar:%{_javadir}/javapoet.jar:%{_javadir}/incap.jar:%{_javadir}/escapevelocity.jar"
EXPORTS=(
	--add-exports=java.base/jdk.internal.javac=ALL-UNNAMED
	--add-exports=jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED
	--add-exports=jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED
	--add-exports=jdk.compiler/com.sun.tools.javac.code=ALL-UNNAMED
	--add-exports=jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED
	--add-exports=jdk.compiler/com.sun.tools.javac.comp=ALL-UNNAMED
	--add-exports=jdk.compiler/com.sun.tools.javac.main=ALL-UNNAMED
	--add-exports=jdk.compiler/com.sun.tools.javac.model=ALL-UNNAMED
	--add-exports=jdk.compiler/com.sun.tools.javac.parser=ALL-UNNAMED
	--add-exports=jdk.compiler/com.sun.tools.javac.processing=ALL-UNNAMED
	--add-exports=jdk.compiler/com.sun.tools.javac.tree=ALL-UNNAMED
)
javac "${EXPORTS[@]}" -encoding UTF-8 -proc:full \
	-processor com.google.auto.value.processor.AutoValueProcessor,com.google.auto.value.processor.AutoBuilderProcessor \
	-cp "$AP" -d classes-api -s gen-api @check.list
test "$(find gen-api -name 'AutoValue_*.java' | wc -l)" -ge 1
cat > manifest-api.mf << 'EOF'
Manifest-Version: 1.0
Automatic-Module-Name: com.google.errorprone.checkapi

EOF
jar cfm error_prone_check_api.jar manifest-api.mf -C classes-api .
jar i error_prone_check_api.jar
javap -verbose -cp error_prone_check_api.jar com.google.errorprone.scanner.ScannerSupplier | grep -F 'major version: 71'
jar --describe-module --file error_prone_check_api.jar > describe-api.txt
if grep -F -q 'Unable to derive' describe-api.txt; then
	cat describe-api.txt
	exit 1
fi

cat > error_prone_check_api.pom << EOF
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.google.errorprone</groupId>
  <artifactId>error_prone_check_api</artifactId>
  <version>%{version}</version>
  <name>Error Prone check API</name>
  <description>API for writing Error Prone checks</description>
  <url>https://errorprone.info/</url>
  <licenses>
    <license>
      <name>Apache License, Version 2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>com.google.errorprone</groupId>
      <artifactId>error_prone_annotation</artifactId>
      <version>%{version}</version>
    </dependency>
    <dependency>
      <groupId>com.google.errorprone</groupId>
      <artifactId>error_prone_annotations</artifactId>
      <version>2.50.0</version>
    </dependency>
    <dependency>
      <groupId>com.google.guava</groupId>
      <artifactId>guava</artifactId>
      <version>33.6.0-jre</version>
    </dependency>
    <dependency>
      <groupId>com.github.ben-manes.caffeine</groupId>
      <artifactId>caffeine</artifactId>
      <version>3.0.5</version>
    </dependency>
    <dependency>
      <groupId>io.github.java-diff-utils</groupId>
      <artifactId>java-diff-utils</artifactId>
      <version>4.12</version>
    </dependency>
    <dependency>
      <groupId>org.checkerframework</groupId>
      <artifactId>dataflow</artifactId>
      <version>3.41.0-eisop1</version>
    </dependency>
    <dependency>
      <groupId>org.checkerframework</groupId>
      <artifactId>javacutil</artifactId>
      <version>3.41.0-eisop1</version>
    </dependency>
    <dependency>
      <groupId>com.github.kevinstern</groupId>
      <artifactId>software-and-algorithms</artifactId>
      <version>1.0</version>
    </dependency>
  </dependencies>
</project>
EOF

mkdir -p gen-proto
protoc --java_out=gen-proto -I core/src/main/proto core/src/main/proto/api_diff.proto
test -f gen-proto/com/google/errorprone/bugpatterns/apidiff/ApiDiffProto.java
find core/src/main/java -name '*.java' > core-main.list
test "$(wc -l < core-main.list)" -eq 857
find core/src/main/java gen-proto -name '*.java' > core.list
test "$(wc -l < core.list)" -eq 858
mkdir -p classes-core gen-core
CP="$AP:$PWD/error_prone_check_api.jar:%{_javadir}/google-java-format.jar:%{_javadir}/pcollections.jar:%{_javadir}/auto-service-annotations.jar:%{_javadir}/protobuf-java.jar"
javac "${EXPORTS[@]}" -encoding UTF-8 -proc:full \
	-processor com.google.auto.value.processor.AutoValueProcessor,com.google.auto.value.processor.AutoBuilderProcessor \
	-cp "$CP" -d classes-core -s gen-core @core.list
test "$(find gen-core -name 'AutoValue_*.java' | wc -l)" -ge 1
mkdir -p classes-core/META-INF/services
echo com.google.errorprone.ErrorProneJavacPlugin > classes-core/META-INF/services/com.sun.source.util.Plugin
/bin/cp -f core/src/main/java/com/google/errorprone/bugpatterns/apidiff/8-to-lts-diff.binarypb \
	classes-core/com/google/errorprone/bugpatterns/apidiff/8-to-lts-diff.binarypb
cat > manifest-core.mf << 'EOF'
Manifest-Version: 1.0
Automatic-Module-Name: com.google.errorprone.core

EOF
jar cfm error_prone_core.jar manifest-core.mf -C classes-core .
jar i error_prone_core.jar
jar tf error_prone_core.jar | grep -F -q 'META-INF/services/com.sun.source.util.Plugin'
jar tf error_prone_core.jar | grep -F -q 'com/google/errorprone/bugpatterns/apidiff/8-to-lts-diff.binarypb'
javap -verbose -cp error_prone_core.jar com.google.errorprone.ErrorProneJavacPlugin | grep -F 'major version: 71'
jar --describe-module --file error_prone_core.jar > describe-core.txt
if grep -F -q 'Unable to derive' describe-core.txt; then
	cat describe-core.txt
	exit 1
fi

cat > error_prone_core.pom << EOF
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.google.errorprone</groupId>
  <artifactId>error_prone_core</artifactId>
  <version>%{version}</version>
  <name>Error Prone core</name>
  <description>Error Prone checks and javac plugin</description>
  <url>https://errorprone.info/</url>
  <licenses>
    <license>
      <name>Apache License, Version 2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>com.google.errorprone</groupId>
      <artifactId>error_prone_annotation</artifactId>
      <version>%{version}</version>
    </dependency>
    <dependency>
      <groupId>com.google.errorprone</groupId>
      <artifactId>error_prone_check_api</artifactId>
      <version>%{version}</version>
    </dependency>
    <dependency>
      <groupId>com.google.errorprone</groupId>
      <artifactId>error_prone_annotations</artifactId>
      <version>2.50.0</version>
    </dependency>
    <dependency>
      <groupId>com.google.guava</groupId>
      <artifactId>guava</artifactId>
      <version>33.6.0-jre</version>
    </dependency>
    <dependency>
      <groupId>com.google.auto.value</groupId>
      <artifactId>auto-value-annotations</artifactId>
      <version>1.11.1</version>
    </dependency>
    <dependency>
      <groupId>com.google.auto</groupId>
      <artifactId>auto-common</artifactId>
      <version>1.2.2</version>
    </dependency>
    <dependency>
      <groupId>com.google.googlejavaformat</groupId>
      <artifactId>google-java-format</artifactId>
      <version>1.35.0</version>
    </dependency>
    <dependency>
      <groupId>com.google.protobuf</groupId>
      <artifactId>protobuf-java</artifactId>
      <version>4.33.2</version>
    </dependency>
    <dependency>
      <groupId>javax.inject</groupId>
      <artifactId>javax.inject</artifactId>
      <version>1.0.5</version>
    </dependency>
    <dependency>
      <groupId>org.pcollections</groupId>
      <artifactId>pcollections</artifactId>
      <version>4.0.1</version>
    </dependency>
    <dependency>
      <groupId>com.github.kevinstern</groupId>
      <artifactId>software-and-algorithms</artifactId>
      <version>1.0</version>
    </dependency>
  </dependencies>
</project>
EOF

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact error_prone_annotation.pom:error_prone_annotation.jar \
	--file-name error_prone_annotation \
	--filelist .mfiles
sysjar install --buildroot %{buildroot} \
	--artifact error_prone_check_api.pom:error_prone_check_api.jar \
	--file-name error_prone_check_api \
	--filelist .mfiles-api
sysjar install --buildroot %{buildroot} \
	--artifact error_prone_core.pom:error_prone_core.jar \
	--file-name error_prone_core \
	--filelist .mfiles-core
while IFS= read -r line; do
	grep -qxF "$line" .mfiles || printf '%%s\n' "$line" >> .mfiles
done < .mfiles-api
while IFS= read -r line; do
	grep -qxF "$line" .mfiles || printf '%%s\n' "$line" >> .mfiles
done < .mfiles-core

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
ANN=%{buildroot}%{_javadir}/error_prone_annotation.jar
API=%{buildroot}%{_javadir}/error_prone_check_api.jar
CORE=%{buildroot}%{_javadir}/error_prone_core.jar
test -f "$ANN"
test -f "$API"
test -f "$CORE"
mkdir -p check
cat > check/Ann.java << 'EOF'
import com.google.errorprone.BugPattern;
import com.google.errorprone.BugPattern.LinkType;
import com.google.errorprone.BugPattern.SeverityLevel;
import com.google.errorprone.BugPatternValidator;
@BugPattern(name = "GradleCheck", summary = "gradle", severity = SeverityLevel.ERROR, linkType = LinkType.NONE)
class Sample {}
public class Ann {
	public static void main(String[] args) throws Exception {
		BugPattern pattern = Sample.class.getAnnotation(BugPattern.class);
		BugPatternValidator.validate(pattern);
		System.out.println("epann_ok " + pattern.name() + " " + pattern.summary());
	}
}
EOF
ACP="$ANN:%{_javadir}/guava.jar"
javac --release 21 -encoding UTF-8 -cp "$ACP" -d check check/Ann.java
java -cp "check:$ACP" Ann > check/ann.txt
cat check/ann.txt
grep -F -q 'epann_ok GradleCheck gradle' check/ann.txt

cat > check/Core.java << 'EOF'
import com.google.common.io.Resources;
import com.google.errorprone.bugpatterns.apidiff.ApiDiffProto;
import com.google.errorprone.bugpatterns.apidiff.Java8ApiChecker;
import com.google.errorprone.scanner.BuiltInCheckerSuppliers;
import com.google.errorprone.scanner.ScannerSupplier;
import com.google.protobuf.ExtensionRegistry;

public class Core {
	public static void main(String[] args) throws Exception {
		ScannerSupplier errors = BuiltInCheckerSuppliers.errorChecks();
		int n = errors.getEnabledChecks().size();
		byte[] data = Resources.toByteArray(
			Resources.getResource(Java8ApiChecker.class, "8-to-lts-diff.binarypb"));
		ApiDiffProto.Diff diff = ApiDiffProto.Diff.newBuilder()
			.mergeFrom(data, ExtensionRegistry.getEmptyRegistry())
			.build();
		int classes = diff.getClassDiffCount();
		if (n < 100 || classes < 1) {
			throw new AssertionError("n=" + n + " classes=" + classes);
		}
		System.out.println("epcore_ok " + n + " " + classes);
	}
}
EOF
CCP="$CORE:$API:$ANN:%{_javadir}/error_prone_annotations-2.50.0.jar:%{_javadir}/guava.jar:%{_javadir}/failureaccess.jar:%{_javadir}/auto-value-annotations.jar:%{_javadir}/auto-common.jar:%{_javadir}/google-java-format.jar:%{_javadir}/pcollections.jar:%{_javadir}/atinject.jar:%{_javadir}/caffeine.jar:%{_javadir}/java-diff-utils.jar:%{_javadir}/dataflow.jar:%{_javadir}/software-and-algorithms.jar:%{_javadir}/javacutil.jar:%{_javadir}/checker-qual-3.41.0-eisop1.jar:%{_javadir}/plume-util.jar:%{_javadir}/protobuf-java.jar"
javac --release 21 -encoding UTF-8 -cp "$CCP" -d check check/Core.java
java -cp "check:$CCP" Core > check/core.txt
cat check/core.txt
grep -E -q '^epcore_ok [0-9]+ [0-9]+$' check/core.txt

%files -f .mfiles
%license COPYING
%doc README.md
