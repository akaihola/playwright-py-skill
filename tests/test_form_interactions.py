"""Tests for Form Interactions examples from API_REFERENCE.md."""

import tempfile
import os
from pathlib import Path
from conftest import extract_markdown_code, get_action_log, DummyBrowser


def extract_form_interactions_code():
    """Extract Form Interactions examples from API_REFERENCE.md.

    Returns:
        Modified code ready for execution
    """
    return extract_markdown_code(
        "Form Interactions",
        expected_substrings=[
            "page.get_by_label(\"Email\").fill('user@example.com')",
            "page.get_by_placeholder(\"Enter your name\").fill('John Doe')",
            "page.locator('#username').clear()",
            "page.locator('#username').type('newuser', delay=100)",
            'page.get_by_label("I agree").check()',
            'page.get_by_label("Subscribe").uncheck()',
            'page.get_by_label("Option 2").check()',
            "page.select_option('select#country', 'usa')",
            "page.select_option('select#country', label=\"United States\")",
            "page.select_option('select#country', index=2)",
            "page.select_option('select#colors', ['red', 'blue', 'green'])",
            "page.set_input_files('input[type=\"file\"]', 'path/to/file.pdf')",
            "page.set_input_files('#file-upload-multiple', ['file1.pdf', 'file2.pdf'])",
        ],
    )


class TestFormInteractions:
    """Tests for the Form Interactions examples."""

    def test_form_interactions_examples(self, test_server_url, page):
        """Test Form Interactions examples from API_REFERENCE.md.

        This test:
        - Extracts code from API_REFERENCE.md at runtime
        - Executes all form interaction examples in sequence
        - Verifies all events are logged correctly:
          * Text input fills (label and placeholder)
          * Clear and type with delay
          * Checkbox check/uncheck
          * Radio button selection
          * Select dropdown (value, label, index)
          * Multi-select
          * File upload (single and multiple)
        """
        extracted_code = extract_form_interactions_code()

        page.goto(f"{test_server_url}/form-interactions")
        page.locator("#action-log").wait_for(state="visible")

        # Create temporary test files for upload
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file1 = Path(tmpdir) / "test.pdf"
            test_file1.write_text("Test file content 1")

            test_file2 = Path(tmpdir) / "file1.pdf"
            test_file2.write_text("Test file content 2")

            test_file3 = Path(tmpdir) / "file2.pdf"
            test_file3.write_text("Test file content 3")

            # Modify and execute Form Interactions code from API_REFERENCE.md
            # Replace file paths with actual temporary files
            lines = extracted_code.split("\n")
            modified_code = []
            found_single_file = False
            found_multiple_files = False
            for line in lines:
                stripped_line = line.strip()

                # Skip blank lines
                if not stripped_line:
                    continue

                # Skip comment lines
                if stripped_line.startswith("#"):
                    continue

                if "'path/to/file.pdf'" in line:
                    found_single_file = True
                    modified_code.append(
                        line.replace("'path/to/file.pdf'", f"'{test_file1}'")
                    )
                elif "['file1.pdf', 'file2.pdf']" in line:
                    found_multiple_files = True
                    modified_code.append(
                        line.replace(
                            "['file1.pdf', 'file2.pdf']",
                            f"[r'{test_file2}', r'{test_file3}']",
                        )
                    )
                elif "set_input_files" in line:
                    assert False, f"Unrecognized line with file reference: {line}"
                else:
                    modified_code.append(line)

            assert found_single_file, "Expected to find single file upload pattern"
            assert found_multiple_files, "Expected to find multiple file upload pattern"

            exec("\n".join(modified_code), {"page": page, "browser": DummyBrowser()})

        # Get action log and verify
        log_lines = get_action_log(page)

        # Expected log entries
        expected_log = [
            "fill email user@example.com",
            "change email user@example.com",
            "fill name John Doe",
            "change name John Doe",
            "fill username",  # clear (empty value)
            "fill username n",  # type with delay (first character)
            "fill username ne",  # type with delay
            "fill username new",  # type with delay
            "fill username newu",  # type with delay
            "fill username newus",  # type with delay
            "fill username newuse",  # type with delay
            "fill username newuser",  # type with delay
            "change username newuser",
            "check agree",  # check checkbox by label
            "uncheck subscribe",  # uncheck checkbox by label
            "select option option2",  # select radio button by label
            "select country usa",  # select by value
            "select country usa",  # select by label (same value)
            "select country france",  # select by index (2)
            "select colors red,blue,green",  # multi-select
            f"upload file-upload {test_file1.name}:19",  # single file upload
            f"upload file-upload-multiple {test_file2.name}:19,{test_file3.name}:19",  # multiple file upload
        ]

        assert log_lines == expected_log
