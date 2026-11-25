#  SPDX-License-Identifier: GPL-3.0+
#
# Copyright © 2026 nudel contributors.
#
# This file is part of nudel.
#
# nudel is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# nudel is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with nudel.  If not, see <http://www.gnu.org/licenses/>.

"""Regression tests for comment parsing in ``nudel.core``."""

from __future__ import annotations

from nudel.comments import CommentSymbol
from nudel.core import ENSDF, Dataset
from nudel.provider import ENSDFInMemoryProvider

NUCID = "50019"
DATASET_ID = "ADOPTED LEVELS"
NUCLEUS = (500, 119)
LEVEL = "50019  L   0.0    0+     STABLE".ljust(80)


def _comment(cont: str, flag: str, text: str) -> str:
    return f"{NUCID}{cont}{flag}  {text}".ljust(80)


def _old_format(lhs: str, text: str, flag: str = "c") -> str:
    assert len(lhs) == 10
    return f"{NUCID} {flag}  {lhs}{text}".ljust(80)


def _parse(*records: str) -> Dataset:
    header = f"{NUCID}    {DATASET_ID}".ljust(80)
    dataset = "\n".join([header, *records]) + "\n"
    provider = ENSDFInMemoryProvider({(NUCLEUS, DATASET_ID): dataset})
    ensdf = ENSDF(provider=provider)
    ENSDF.active_ensdf = ensdf
    try:
        return ensdf.get_dataset(NUCLEUS, DATASET_ID)
    finally:
        ENSDF.active_ensdf = None


def test_general_modern_comment():
    line = _comment(" ", "c", "Just some text")

    dataset = _parse(line)

    assert len(dataset.header_comments) == 1
    comment = dataset.header_comments[0]
    assert comment.kind == "c"
    assert comment.rtype == ""
    assert comment.particle == ""
    assert comment.text == "Just some text"
    assert comment.symbols == ()
    assert comment.key is None
    assert comment.label is None
    assert comment.raw == (line,)


def test_general_old_reference_list_is_not_structured():
    line = _old_format("2005Sa06, ", "reference list text")

    dataset = _parse(line)

    comment = dataset.header_comments[0]
    assert comment.symbols == ()
    assert comment.key is None
    assert "reference list text" in comment.text


def test_old_format_prose_is_plain_comment():
    line = _comment(" ", "c", "The April 2004 conference report")

    dataset = _parse(line)

    comment = dataset.header_comments[0]
    assert comment.symbols == ()
    assert comment.key is None
    assert "April 2004 conference report" in comment.text


def test_titl_modern_key():
    dataset = _parse(_comment(" ", "c", "TITL$Some title"))

    comment = dataset.header_comments[0]
    assert comment.key == "TITL"
    assert comment.text == "Some title"
    assert comment.symbols == ()
    assert dataset.general_comments_by_key["TITL"] == [comment]


def test_t_text_preserves_spacing_and_concatenates():
    primary = _comment(" ", "t", " raw text ")
    continuation = _comment("2", "t", " more ")

    dataset = _parse(primary, continuation)

    comment = dataset.header_comments[0]
    assert comment.kind == "t"
    assert comment.text == primary[9:] + continuation[9:]


def test_c_continuation_joins_with_one_space():
    primary = _comment(" ", "c", "first part")
    continuation = _comment("2", "c", "second part")

    dataset = _parse(primary, continuation)

    assert dataset.header_comments[0].text == "first part second part"


def test_d_continuation_joins_with_one_space():
    primary = _comment(" ", "d", "first part")
    continuation = _comment("2", "d", "second part")

    dataset = _parse(primary, continuation)

    comment = dataset.header_comments[0]
    assert comment.kind == "d"
    assert comment.text == "first part second part"


def test_field_symbols_modern():
    dataset = _parse(
        _comment(" ", "c", "E$energy text"),
        _comment(" ", "c", "E,DE$comma list"),
        _comment(" ", "c", "%B-,Q-$decay modes"),
    )

    assert dataset.header_comments[0].symbols == (CommentSymbol("E"),)
    assert dataset.header_comments[1].symbols == (
        CommentSymbol("E"),
        CommentSymbol("DE"),
    )
    assert dataset.header_comments[2].symbols == (
        CommentSymbol("%B-"),
        CommentSymbol("Q-"),
    )
    assert dataset.header_comments[0].text == "energy text"
    assert dataset.header_comments[2].text == "decay modes"


def test_repeated_field_keeps_both_comments():
    dataset = _parse(
        _comment(" ", "c", "E$first"),
        _comment(" ", "c", "E$second"),
        _comment(" ", "c", "E(A)$flagged first"),
        _comment(" ", "c", "E(A)$flagged second"),
    )

    assert [c.text for c in dataset.comments_by_field["E"]] == [
        "first",
        "second",
        "flagged first",
        "flagged second",
    ]
    assert [c.text for c in dataset.comments_by_field_flag[("E", "A")]] == [
        "flagged first",
        "flagged second",
    ]


def test_symbol_flags():
    cases = {
        "E(A)$text": (CommentSymbol("E", ("A",)),),
        "E(A),J(B)$text": (
            CommentSymbol("E", ("A",)),
            CommentSymbol("J", ("B",)),
        ),
        "S(AB)$text": (CommentSymbol("S", ("A", "B")),),
        "S(A,B)$text": (CommentSymbol("S", ("A", "B")),),
        "S(A, B)$text": (CommentSymbol("S", ("A", "B")),),
        "BAND(C)$text": (CommentSymbol("BAND", ("C",)),),
    }

    for text, expected in cases.items():
        dataset = _parse(_comment(" ", "c", text))
        assert dataset.header_comments[0].symbols == expected


def test_field_flag_keys_are_distinct():
    dataset = _parse(
        _comment(" ", "c", "E(E)$first"),
        _comment(" ", "c", "RI(E)$second"),
    )

    assert [c.text for c in dataset.comments_by_field_flag[("E", "E")]] == ["first"]
    assert [c.text for c in dataset.comments_by_field_flag[("RI", "E")]] == ["second"]
    assert len(dataset.comments_by_flag["E"]) == 2


def test_relabel_sets_label_and_field_labels():
    primary = _comment(" ", "c", "T$LABEL=First part")
    continuation = _comment("2", "c", "second part")

    dataset = _parse(primary, continuation)

    comment = dataset.header_comments[0]
    assert comment.label == "First part second part"
    assert comment.text == "First part second part"
    assert comment.symbols == (CommentSymbol("T"),)
    assert comment.key is None
    assert dataset.field_labels == {"T": "First part second part"}
    assert dataset.comments_by_field["T"] == [comment]


def test_body_comments_attach_to_preceding_record():
    dataset = _parse(LEVEL, _comment(" ", "c", "E$body text"))

    assert dataset.header_comments == []
    assert len(dataset.levels[0].parsed_comments) == 1
    comment = dataset.levels[0].parsed_comments[0]
    assert comment.text == "body text"
    assert comment.symbols == (CommentSymbol("E"),)
    assert comment in dataset.parsed_comments
    assert dataset.comments_by_field["E"] == [comment]


def test_header_comments_do_not_attach_to_record():
    dataset = _parse(_comment(" ", "c", "E$header text"), LEVEL)

    assert len(dataset.header_comments) == 1
    assert dataset.header_comments[0].text == "header text"
    assert dataset.levels[0].parsed_comments == []


def test_old_format_field_list():
    dataset = _parse(_old_format("E,DE      ", "footnote text"))

    assert dataset.header_comments[0].symbols == (
        CommentSymbol("E"),
        CommentSymbol("DE"),
    )
    assert dataset.header_comments[0].text == "footnote text"


def test_old_format_single_field():
    dataset = _parse(_old_format("E         ", "single field text"))

    assert dataset.header_comments[0].symbols == (CommentSymbol("E"),)
    assert dataset.header_comments[0].text == "single field text"


def test_old_format_titl_key():
    dataset = _parse(_old_format("TITL      ", "general text"))

    assert dataset.header_comments[0].key == "TITL"
    assert dataset.header_comments[0].symbols == ()
    assert dataset.header_comments[0].text == "general text"


def test_raw_lines_are_retained_unchanged():
    primary = _comment(" ", "c", "E$first")
    continuation = _comment("2", "c", "second")

    dataset = _parse(primary, continuation)

    assert dataset.header_comments[0].raw == (primary, continuation)


def test_malformed_modern_lhs_keeps_rhs_text():
    for lhs in ("B- EAV,LOGFT", "E, not a field", "E(A"):
        dataset = _parse(_comment(" ", "c", f"{lhs}$text"))

        comment = dataset.header_comments[0]
        assert comment.text == "text"
        assert comment.symbols == ()
        assert comment.key is None


def test_empty_rhs_keeps_comment():
    for lhs in ("S", "T", "E,DE"):
        dataset = _parse(_comment(" ", "c", f"{lhs}$"))

        comment = dataset.header_comments[0]
        assert comment.text == ""
        assert comment.symbols


def test_orphan_continuation_does_not_abort():
    orphan = _comment("2", "c", "orphan continuation")

    dataset = _parse(orphan)

    assert dataset.comments == [[orphan]]
    assert dataset.header_comments[0].text == "orphan continuation"


def test_short_line_does_not_abort():
    short = "50019 c  short"

    dataset = _parse(short)

    assert dataset.comments == [[short]]
    assert dataset.header_comments[0].text == "short"


def test_column_six_one_starts_new_comment_group():
    first = _comment(" ", "c", "first comment")
    second = _comment("1", "c", "second comment")

    dataset = _parse(first, second)

    assert dataset.comments == [[first], [second]]
    assert [c.text for c in dataset.header_comments] == [
        "first comment",
        "second comment",
    ]


def test_comments_for():
    dataset = _parse(
        _comment(" ", "c", "E(A)$first"),
        _comment(" ", "c", "RI(A)$second"),
        _comment(" ", "c", "Just general text"),
    )

    assert dataset.comments_for() == dataset.parsed_comments
    assert dataset.comments_for() is not dataset.parsed_comments
    assert [c.text for c in dataset.comments_for(field="E")] == ["first"]
    assert [c.text for c in dataset.comments_for(flag="A")] == ["first", "second"]
    assert [c.text for c in dataset.comments_for(field="E", flag="A")] == ["first"]
    assert dataset.comments_for(field="E", flag="B") == []
    assert dataset.comments_for(field="X") == []
    assert dataset.comments_for(flag="Z") == []


def test_header_non_comment_records_are_parsed():
    history = f"{NUCID}  H TYP=FUL$AUT=J. Smith$DAT=2026$"
    qvalue = f"{NUCID}  Q     -1500050    420030    580040    3200    60"
    xref = f"{NUCID}  XA500OG B- DECAY"
    reference = f"{NUCID}  R 88SM01  J. Smith, Synth. Nucl. Data, 2026, Vol 1, p500"
    parent = (
        f"{NUCID}  P        0.0  0+                    1.5 MS     5"
        "               1520050"
    )
    normalization = f"{NUCID}  N        1.0 1     1.0 1     100 1"

    dataset = _parse(
        history.ljust(80),
        qvalue.ljust(80),
        xref.ljust(80),
        reference.ljust(80),
        parent.ljust(80),
        normalization.ljust(80),
    )

    assert dataset.history == {"TYP": "FUL", "AUT": "J. Smith", "DAT": "2026"}
    assert dataset.qrecords
    assert dataset.cross_references
    assert dataset.references
    assert dataset.parents
    assert dataset.normalization_records


def test_level_c_column_flag_is_footnote_flag():
    level = list(LEVEL)
    level[76] = "A"

    dataset = _parse("".join(level))

    assert dataset.levels[0].footnote_flags == ["A"]


def test_level_flag_continuation_appends_footnote_flags():
    level = list(LEVEL)
    level[76] = "C"
    flag_line = f"{NUCID}2 L FLAG=AB".ljust(80)

    dataset = _parse("".join(level), flag_line)

    assert dataset.levels[0].footnote_flags == ["C", "A", "B"]


GAMMA = "50019  G      156.4 4     100  [E1]                    1.28E-3 2".ljust(80)
BETA = "50019  B      1520050     100 1              6.42     1".ljust(80)


def _flag_line(rectype: str, flags: str) -> str:
    return f"{NUCID}2 {rectype} FLAG={flags}".ljust(80)


def test_gamma_c_column_flags_ignore_reserved_symbols():
    for reserved in "*&@%":
        gamma = list(GAMMA)
        gamma[76] = reserved

        dataset = _parse("".join(gamma))

        assert dataset.records[0].footnote_flags == []


def test_gamma_c_column_letter_is_footnote_flag():
    gamma = list(GAMMA)
    gamma[76] = "A"

    dataset = _parse("".join(gamma))

    assert dataset.records[0].footnote_flags == ["A"]


def test_gamma_flag_continuation_contributes():
    gamma = list(GAMMA)
    gamma[76] = "C"

    dataset = _parse("".join(gamma), _flag_line("G", "AB"))

    assert dataset.records[0].footnote_flags == ["C", "A", "B"]


def test_beta_c_column_is_not_a_footnote_flag():
    beta = list(BETA)
    beta[76] = "A"

    dataset = _parse("".join(beta))

    assert dataset.records[0].footnote_flags == []


def test_beta_flag_continuation_contributes():
    beta = list(BETA)
    beta[76] = "Z"

    dataset = _parse("".join(beta), _flag_line("B", "AB"))

    assert dataset.records[0].footnote_flags == ["A", "B"]


def test_flag_continuation_accepts_separators():
    for flags in ("AB", "A,B", "A B"):
        level = list(LEVEL)
        level[76] = "C"

        dataset = _parse("".join(level), _flag_line("L", flags))

        assert dataset.levels[0].footnote_flags == ["C", "A", "B"]


def test_footnotes_for_resolves_by_field_and_flag():
    level = list(LEVEL)
    level[76] = "E"

    dataset = _parse(
        _comment(" ", "c", "E(E)$first"),
        _comment(" ", "c", "RI(E)$second"),
        "".join(level),
    )

    record = dataset.levels[0]
    assert [c.text for c in record.footnotes_for("E")] == ["first"]
    assert [c.text for c in record.footnotes_for("RI")] == ["second"]
    assert record.footnotes_for("J") == []


def test_footnotes_for_without_flags_is_empty():
    dataset = _parse(_comment(" ", "c", "E(A)$first"), LEVEL)

    assert dataset.levels[0].footnotes_for("E") == []


def test_footnotes_for_keeps_duplicate_field_flag_comments():
    level = list(LEVEL)
    level[76] = "A"

    dataset = _parse(
        _comment(" ", "c", "E(A)$first"),
        _comment(" ", "c", "E(A)$second"),
        "".join(level),
    )

    first, second = dataset.comments_by_field_flag[("E", "A")]
    assert first is not second
    assert dataset.levels[0].footnotes_for("E") == [first, second]
