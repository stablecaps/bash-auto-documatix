import logging
from dataclasses import dataclass

from bashautodoc.function_dependency_processor import FunctionDependencyProcessor

LOG = logging.getLogger(__name__)


# TODO: enable slots=True
# @dataclass(slots=True)
@dataclass()
class FunctionDataHolder:
    srcfile_relpath: str = None
    #
    func_name_list: list[str] = None
    full_alias_str_list: list[str] = None
    cite_about: str = None
    func_text_dict: dict[str, str] = None
    func_dep_dict: dict[str, list[str]] = None


class FunctionDatahandler:
    def __new__(cls, srcfile_relpath: str):
        # https://stackoverflow.com/questions/2491819/how-to-return-a-value-from-init-in-python
        cls.funcdata = FunctionDataHolder()
        cls.funcdata.srcfile_relpath = srcfile_relpath

        return cls.main()

    @staticmethod
    def get_function_name(line_str):
        """
        Extracts the function name from a line of shell script.

        Args:
            line_str (str): A line of shell script.

        Returns:
            str: The name of the function.

        Example:
            function_name = ShellSrcPreProcessor.get_function_name("function hello_world {")
        """
        func_name = None
        if line_str.strip().endswith(("{", "}")):
            function_header = line_str.split()
            func_name = function_header[1].strip("()")
            LOG.debug("func_name: %s", func_name)
        return func_name

    @staticmethod
    def _process_about_line(line):
        """
        Process a line of code containing an "about" statement.

        Args:
            line (str): Line of code.

        Returns:
            str: Processed about statement.

        Example:
            preprocessor = ShellSrcPreProcessor(conf="config",
                                                cleaned_srcfiles_relpaths=["file1", "file2"],
                                                project_docs_dir="docs/",
                                                debug=True)
            about_statement = preprocessor._process_about_line("about-plugin 'This is a plugin'")
        """
        return (
            line.replace("about-plugin", "")
            .replace("about-alias", "")
            .replace("about-completion", "")
            .replace("about-module", "")
            .replace("about-internal", "")
            .replace("'", "")
            .strip()
        )

    @staticmethod
    def _process_alias_line(line):
        """
        Process a line of code containing an alias definition.

        Args:
            line (str): Line of code.

        Returns:
            str: Processed alias string.

        Example:
            preprocessor = ShellSrcPreProcessor(conf="config",
                                                cleaned_srcfiles_relpaths=["file1", "file2"],
                                                project_docs_dir="docs/",
                                                debug=True)
            alias_string = preprocessor._process_alias_line("alias ls='ls -l' # List files")
        """
        LOG.debug("line: %s", line)

        alias_list = line.replace("alias ", "").strip().split("=", 1)
        LOG.debug("alias_list: %s", alias_list)

        if len(alias_list) < 2:
            return None

        alias_name = alias_list[0]
        alias_cmd = alias_list[1]
        alias_comment = ""

        if "#" in alias_list[1]:
            alias_list_lvl2 = alias_list[1].split("#", 1)
            alias_cmd = alias_list_lvl2[0]
            alias_comment = alias_list_lvl2[1]

        return f"| **{alias_name}** | `{alias_cmd[1:-1]}` | {alias_comment}\n"

    @classmethod
    def create_func_text_dict(cls):
        """
        Create a dictionary of function names and their corresponding code.

        Args:
            srcfile_relpath (str): Path to the src file.

        Returns:
            tuple: Tuple containing function name list, alias string list,
                   about citation, and function text dictionary.

        Example:
            preprocessor = ShellSrcPreProcessor(conf="config",
                                                cleaned_srcfiles_relpaths=["file1", "file2"],
                                                project_docs_dir="docs/",
                                                debug=True)
            func_name_list, alias_str_list, cite_about, func_text_dict =
                preprocessor.create_func_text_dict("file1")
        """
        func_name_list = []
        full_alias_str_list = []
        func_name = None
        cite_about = "Undefined. Add composure cite-about to shell script file"

        with open(cls.funcdata.srcfile_relpath, "r") as FHI:
            LOG.debug("cls.funcdata.srcfile_relpath: %s", cls.funcdata.srcfile_relpath)

            func_text_dict = {}
            src_text = FHI.read()

            for line in src_text.split("\n"):
                if line.startswith("function"):
                    func_name = FunctionDatahandler.get_function_name(line)
                    if func_name is not None:
                        func_name_list.append(func_name)
                        func_text_dict[func_name] = line
                # TODO: remove hardcoded "about" strings
                elif line.startswith(
                    (
                        "about-plugin",
                        "about-alias",
                        "about-completion",
                        "about-module",
                        "about-internal",
                    )
                ):
                    cite_about = FunctionDatahandler._process_about_line(line)
                elif line.startswith("alias"):
                    alias_str = FunctionDatahandler._process_alias_line(line)
                    if alias_str is not None:
                        full_alias_str_list.append(alias_str)
                else:
                    if func_name is not None:
                        func_text_dict[func_name] += "\n" + line

        cls.funcdata.func_name_list = func_name_list
        cls.funcdata.full_alias_str_list = full_alias_str_list
        cls.funcdata.cite_about = cite_about
        cls.funcdata.func_text_dict = func_text_dict
        # return func_name_list, full_alias_str_list, cite_about, func_text_dict

    @classmethod
    def main(cls):
        cls.create_func_text_dict()

        func_dep_processor = FunctionDependencyProcessor(
            func_name_list=cls.funcdata.func_name_list,
            func_text_dict=cls.funcdata.func_text_dict,
        )
        cls.funcdata.func_dep_dict = func_dep_processor.create_func_dep_dict()

        return cls.funcdata
