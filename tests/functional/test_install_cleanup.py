import os
from os.path import exists

import pytest

from pip._internal.cli.status_codes import PREVIOUS_BUILD_DIR_ERROR


@pytest.mark.network
def test_no_clean_option_blocks_cleaning_after_install(script, data):
    """
    Test --no-clean option blocks cleaning after install
    """
    build = script.base_path / 'pip-build'
    script.pip(
        'install', '--no-clean', '--no-index', '--build', build,
        '--find-links={}'.format(data.find_links), 'simple',
        expect_temp=True,
        # TODO: expect_stderr_warning is used for the --build deprecation,
        #       remove it when removing support for --build
        expect_stderr_warning=True,
    )
    assert exists(build)


@pytest.mark.network
def test_cleanup_prevented_upon_build_dir_exception(
    script,
    data,
    use_new_resolver,
):
    """
    Test no cleanup occurs after a PreviousBuildDirError
    """
    build = script.venv_path / 'build'
    build_simple = build / 'simple'
    os.makedirs(build_simple)
    build_simple.joinpath("setup.py").write_text("#")
    result = script.pip(
        'install', '-f', data.find_links, '--no-index', 'simple',
        '--build', build,
        expect_error=(not use_new_resolver),
        expect_temp=(not use_new_resolver),
        expect_stderr=True,
    )

    assert (
        "The -b/--build/--build-dir/--build-directory "
        "option is deprecated."
    ) in result.stderr

    if not use_new_resolver:
        assert result.returncode == PREVIOUS_BUILD_DIR_ERROR, str(result)
        assert "pip can't proceed" in result.stderr, str(result)
        assert exists(build_simple), str(result)


@pytest.mark.network
def test_pep517_no_legacy_cleanup(script, data, with_wheel):
    """Test a PEP 517 failed build does not attempt a legacy cleanup"""
    to_install = data.packages.joinpath('pep517_wrapper_buildsys')
    script.environ["PIP_TEST_FAIL_BUILD_WHEEL"] = "1"
    res = script.pip(
        'install', '-f', data.find_links, to_install,
        expect_error=True
    )
    # Must not have built the package
    expected = "Failed building wheel for pep517-wrapper-buildsys"
    assert expected in str(res)
    # Must not have attempted legacy cleanup
    assert "setup.py clean" not in str(res)
