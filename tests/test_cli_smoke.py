"""Smoke tests for CLI subcommands"""

import subprocess
import sys


def run_kwxlc(*args):
    result = subprocess.run(
        [sys.executable, "-m", "kiwix_llm_cli.cli", *args],
        capture_output=True,
        text=True,
    )
    return result


def test_kwxlc_help():
    result = run_kwxlc("-h")
    assert result.returncode == 0
    assert "kiwix-llm-cli" in result.stdout
    assert "init" in result.stdout
    assert "search" in result.stdout


def test_init_help():
    result = run_kwxlc("init", "-h")
    assert result.returncode == 0
    assert "--bare" in result.stdout


def test_list_help():
    result = run_kwxlc("list", "-h")
    assert result.returncode == 0
    assert "--format" in result.stdout


def test_delete_help():
    result = run_kwxlc("delete", "-h")
    assert result.returncode == 0
    assert "names" in result.stdout
    assert "--force" in result.stdout


def test_search_help():
    result = run_kwxlc("search", "-h")
    assert result.returncode == 0
    assert "query" in result.stdout


def test_suggest_help():
    result = run_kwxlc("suggest", "-h")
    assert result.returncode == 0
    assert "term" in result.stdout


def test_info_help():
    result = run_kwxlc("info", "-h")
    assert result.returncode == 0
    assert "--zim" in result.stdout


def test_get_help():
    result = run_kwxlc("get", "-h")
    assert result.returncode == 0
    assert "title" in result.stdout


def test_install_skills_help():
    result = run_kwxlc("install-skills", "-h")
    assert result.returncode == 0
    assert "--agent" in result.stdout


def test_remote_help():
    result = run_kwxlc("remote", "-h")
    assert result.returncode == 0
    assert "Remote" in result.stdout


def test_remote_catalog_help():
    result = run_kwxlc("remote", "catalog", "-h")
    assert result.returncode == 0
    assert "--lang" in result.stdout


def test_remote_download_help():
    result = run_kwxlc("remote", "download", "-h")
    assert result.returncode == 0
    assert "zim_name" in result.stdout


def test_init_bare():
    result = run_kwxlc("init", "--bare")
    assert result.returncode == 0
    assert "search_dirs" in result.stdout


def test_remote_catalog_lang():
    result = run_kwxlc("remote", "catalog", "--lang", "jpn", "--count", "3")
    assert result.returncode == 0
    assert "Kiwix Library" in result.stdout


def test_remote_catalog_category():
    result = run_kwxlc("remote", "catalog", "--category", "wikipedia", "--count", "3")
    assert result.returncode == 0
    assert "Kiwix Library" in result.stdout
