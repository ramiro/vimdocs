#!/bin/bash

python itervimdocs.py -p ../vim -c ./vimdoc2adoc.py --argument="-e \$encoding" --argument="-o adoc"
bundle exec asciidoctor \
	-D output/html/ \
	-a source-highlighter=pygments \
	-a pygments-style=colorful \
	-a prewrap! \
	-a linkcss \
	-a stylesheet=custom.css \
	-a toc \
	-a sectnums \
	-a sectanchors \
	adoc/*.adoc
cp adoc/asciidoctor.css output/html
