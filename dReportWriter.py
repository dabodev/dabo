from dabo.lib.reporting.reportWriter import ReportWriter
from dabo.common.dObject import dObject

class dReportWriter(dObject, ReportWriter): pass

if __name__ == "__main__":
	## run a test:
	rw = dReportWriter()
	rw.Name = "dReportWriter1"
	rw.OutputName = "./dReportWriter-test.pdf"
	print rw.Name, rw.Application

	xml = """

<report>
	<title>Test Report from dReportWriter</title>

	<testcursor iid="int" cArtist="str">
		<record iid="1" cArtist="The Clash" />
		<record iid="2" cArtist="Queen" />
		<record iid="3" cArtist="Metallica" />
		<record iid="3" cArtist="The Boomtown Rats" />
	</testcursor>

	<page>
		<size>"letter"</size>
		<orientation>"portrait"</orientation>
		<marginLeft>".5 in"</marginLeft>
		<marginRight>".5 in"</marginRight>
		<marginTop>".5 in"</marginTop>
		<marginBottom>".5 in"</marginBottom>
	</page>

	<pageHeader>
		<height>"0.5 in"</height>
		<objects>
			<string>
				<expr>self.ReportForm["title"]</expr>
				<align>"center"</align>
				<x>"3.75 in"</x>
				<y>".3 in"</y>
				<hAnchor>"center"</hAnchor>
				<width>"6 in"</width>
				<height>".25 in"</height>
				<borderWidth>"0 pt"</borderWidth>
				<fontName>"Helvetica"</fontName>
				<fontSize>14</fontSize>
			</string>
		</objects>
	</pageHeader>

	<pageFooter>
		<height>"0.75 in"</height>
		<objects>
			<string>
				<expr>"(also see the test in dabo/lib/reporting)"</expr>
				<align>"right"</align>
				<hAnchor>"right"</hAnchor>
        <x>self.Bands["pageFooter"]["width"]-1</x>
				<y>"0 in"</y>
				<width>"6 in"</width>
			</string>
		</objects>
	</pageFooter>

	<detail>
		<height>".25 in"</height>
		<objects>
			<string>
				<expr>self.Record['cArtist']</expr>
				<width>"6 in"</width>
				<x>"1.25 in"</x>
			</string>
		</objects>
	</detail>

	<pageBackground></pageBackground>

</report>
"""
	rw.ReportFormXML = xml
	rw.UseTestCursor = True
	rw.write()
