#!/usr/bin/env python
import argparse
import codecs
import re
import sys
import textwrap
from os.path import basename, isdir, join, splitext

import attr


SECTION_SEPARATOR_RE = re.compile(r"^={78}$", re.MULTILINE | re.UNICODE)
SECT_TITLE_RE = re.compile(r"^([\d\.]+\.)\s+([A-Za-z \d.-]+)\t+.*$", re.UNICODE)
XREF_TARGET_SEP_RE = re.compile(r"\*\s+\*|\t\*", re.UNICODE)
SUBSECT_TITLE_DETECT_RE = re.compile(
    r"^((?:\d{1,2}\.\d{1,2} )?[A-Z][A-Z -]+\t+.*)$", re.MULTILINE | re.UNICODE
)
SUBSECT_TITLE_RE = re.compile(
    r"^(?:(\d{1,2}\.\d{1,2}) )?([A-Z][A-Z -]+)\t+.*$", re.UNICODE
)
PARA_SEPARATOR_RE = re.compile(r"[\r\n]+")

CODE_EXAMPLE_START_RE = re.compile(r"(?:.* )?>$")

DEBUG = False


@attr.s
class Stats:
    count = attr.ib(default=0)


stats_total = Stats()


def start_literal_block(output):
    output.append("....")


def end_literal_block(output):
    output.append("....")


def mark_unprocessed_text_start(output, context):
    if not context.get("in_unprocessed_text", False):
        start_literal_block(output)
    context["in_unprocessed_text"] = True


def mark_unprocessed_text_end(output, context):
    if context.get("in_unprocessed_text", False):
        end_literal_block(output)
    context["in_unprocessed_text"] = False


class Skip(Exception):
    """A hook raises this exception to signal a line needs to be skipped."""

    pass


class Hook:
    """A generic hook."""

    pass


class CodeExamplesHook(Hook):
    """Hook to detect and format source code example blocks from Vim docs."""

    def init(self):
        self.code_example_state = 0
        self.lines = []

    def emit_code_block(self):
        # TODO: Hard-coded for now. Perhaps we can detect the contained language?
        syntax = "vim"
        output = []
        output.append("[source,%s]" % syntax)
        output.append("----")
        example = "\n".join(self.lines)
        output.extend(textwrap.dedent(example).splitlines(False))
        output.append("----")
        return output

    def process_line(self, line, output, context):
        if self.code_example_state == 2:
            if line and line[0] not in (" ", "\t"):
                # end of a code block
                self.code_example_state = 0
                mark_unprocessed_text_end(output, context)
                if self.lines and not self.lines[0]:
                    self.lines.pop(0)
                output.extend(self.emit_code_block())
                mark_unprocessed_text_start(output, context)
                if line[0] == "<":
                    line = line[1:]
                if not line.rstrip(" \t").endswith(">"):
                    output.append(line)
                    raise Skip
            else:
                self.lines.append(line)
                raise Skip

        if CODE_EXAMPLE_START_RE.match(line):
            # start of a code block
            self.code_example_state = 1
            output.append(line.rstrip(" \t>"))
            self.lines = []
            raise Skip

    def post_process_line(self):
        if self.code_example_state == 1:
            self.code_example_state = 2


def extract_title_and_tags(line):
    """Extract section header and section tags."""
    parts = XREF_TARGET_SEP_RE.split(line)
    tags = []
    for tag in parts[1:]:
        tag = tag.replace("[", r"\[").replace("]", r"\]")
        tags.append(tag.strip("*"))
    title = parts[0].rstrip(" \t")
    return title, tags


def process_file(filename, encoding):
    """Process one Vim documentation file."""
    output = []
    total, hits, misses = 0, 0, 0
    output.append("= %s" % basename(filename))
    output.append("")
    with codecs.open(filename, encoding=encoding) as f:
        contents = f.read()
        total = len(contents.splitlines())
        sections = SECTION_SEPARATOR_RE.split(contents)
        ctx = {"in_unprocessed_text": False}
        for c, section in enumerate(sections):
            if not c:
                processed_text, sub_hits, sub_misses = process_first_section(
                    section, filename, ctx
                )
                output.extend(processed_text)
                hits += sub_hits
                misses += sub_misses
            else:
                hits += 1  # Account for the section separator line
                processed_text, sub_hits, sub_misses = process_section(
                    section, filename, ctx
                )
                output.extend(processed_text)
                hits += sub_hits
                misses += sub_misses
    lines_processed = hits + misses
    print(
        "%s: %d/%d/%d (%d)%s"
        % (
            basename(filename),
            hits,
            misses,
            total,
            lines_processed,
            " !" if lines_processed > total else "",
        )
    )
    return output


def process_first_section(section_text, filename, context):
    """Special treatment for the first top-level section of a Vim doc file."""
    output = []
    hits, misses = 0, 0
    output.append("[discrete]")
    output.append("== First section")
    mark_unprocessed_text_start(output, context)
    for c, line in enumerate(section_text.splitlines(False)):
        output.append(line)
        misses += 1
    mark_unprocessed_text_end(output, context)
    return output, hits, misses


def process_section(section_text, filename, context):
    """Process a Vim doc file top-level section."""
    output = []
    hits, misses = 0, 0
    subsections = SUBSECT_TITLE_DETECT_RE.split(section_text)
    for c, subsection in enumerate(subsections):
        if c and c % 2:
            m = SUBSECT_TITLE_RE.match(subsection)
            if m:
                # Emit subsection title
                subsectnum, subsectitle = m.groups()
                title, tags = extract_title_and_tags(subsectitle)
                stags = "[[%s]]" % ",".join(tags) if tags else ""
                if DEBUG:
                    output.append(
                        "=== %s%s%s"
                        % (stags, title, " (`%s`)" % subsectnum if subsectnum else "")
                    )
                else:
                    output.append("=== %s%s" % (stags, title))
                hits += 1
            else:
                output.append("=== %s" % subsection)
                hits += 1
        elif not c:
            processed_text, sub_hits, sub_misses = process_subsection(
                subsection, filename, context, True
            )
            output.extend(processed_text)
            hits += sub_hits
            misses += sub_misses
        else:
            processed_text, sub_hits, sub_misses = process_subsection(
                subsection, filename, context
            )
            output.extend(processed_text)
            hits += sub_hits
            misses += sub_misses
    return output, hits, misses


def process_subsection(subsection_text, filename, context, is_first_subsection=False):
    """Process a Vim doc file second-level section."""
    output = []
    processed_lines, unprocessed_lines = [], []
    first_line = True

    hook_code = CodeExamplesHook()
    hook_code.init()

    for c, line in enumerate(subsection_text.splitlines(False)):
        if is_first_subsection and c < 2:  # Handle section title or modeline
            if line.rstrip():
                # ignore modeline
                if line.lstrip().startswith("vim:"):
                    processed_lines.append(line)
                    return [], len(processed_lines), len(unprocessed_lines)
                else:
                    # Emit section title
                    m = SECT_TITLE_RE.match(line)
                    if m:
                        sectnum, sectitle = m.groups()
                        title, tags = extract_title_and_tags(sectitle)
                        stags = "[[%s]]" % ",".join(tags) if tags else ""
                        if DEBUG:
                            output.append("== %s%s (`%s`)" % (stags, title, sectnum))
                        else:
                            output.append("== %s%s" % (stags, title))
                    else:
                        title, tags = extract_title_and_tags(line)
                        stags = "[[%s]]" % ",".join(tags) if tags else ""
                        output.append("== %s%s" % (stags, title))

                processed_lines.append(line)
        else:  # Section body
            if first_line:
                mark_unprocessed_text_start(output, context)
                first_line = False

            try:
                hook_code.process_line(line, output, context)
            except Skip:
                processed_lines.append(line)
                continue
            else:
                unprocessed_lines.append(line)
            finally:
                hook_code.post_process_line()
            output.append(line)

    mark_unprocessed_text_end(output, context)
    return output, len(processed_lines), len(unprocessed_lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Convert Vim doc file to Asciidoctor AsciiDoc."
    )
    parser.add_argument("-e", "--encoding", help="file encoding")
    parser.add_argument("-o", "--output-path")
    parser.add_argument("-x", "--output-extension", default="adoc")
    parser.add_argument("-v", "--verbose", help="show more detail", action="store_true")
    parser.add_argument(
        "vimdocfile", metavar="vimdocfile", help="VIM doc file to process"
    )
    args = parser.parse_args()

    if args.verbose:
        print("Processing file %s" % args.vimdocfile)
    try:
        output = process_file(args.vimdocfile, args.encoding)
    except Exception as e:
        print("Error while processing file %s: %s" % (args.vimdocfile, e))
        raise
    final_output = "\n".join(output)
    output_path = args.output_path
    if output_path:
        if isdir(output_path):
            tail = basename(args.vimdocfile)
            head, _ = splitext(tail)
            filename = join(output_path, head + "." + args.output_extension)
        else:
            filename = output_path
        with codecs.open(filename, "w", encoding="utf-8") as f:
            f.write(final_output)
    else:
        print(final_output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
