#  Copyright (c) ZenML GmbH 2021. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at:
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
#  or implied. See the License for the specific language governing
#  permissions and limitations under the License.

import base64
import os
import sys
import tempfile
import webbrowser
from abc import abstractmethod
from typing import Dict, List, Text

import pandas as pd
from facets_overview.generic_feature_statistics_generator import (
    GenericFeatureStatisticsGenerator,
)
from IPython.core.display import HTML, display

from zenml.logger import get_logger
from zenml.post_execution.step import StepView
from zenml.utils import path_utils

logger = get_logger(__name__)


class FacetStatisticsVisualizer:
    """The base implementation of a ZenML Visualizer."""

    @abstractmethod
    def visualize(self, step: StepView, magic: bool = False) -> None:
        """Method to visualize components

        Args:
            step: StepView fetched from run.get_step().
            magic: Whether to render in a Jupyter notebook or not.
        """
        datasets = []
        for output_name, artifact_view in step.outputs.items():
            df = artifact_view.read()
            datasets.append({"name": output_name, "table": df})
        h = self.generate_html(datasets)
        self.generate_facet(h, magic)

    def generate_html(self, datasets: List[Dict[Text, pd.DataFrame]]) -> str:
        """Generates html for facet.

        Args:
            datasets: List of dicts of dataframes to be visualized as stats.

        Returns:
            HTML template with proto string embedded.
        """
        proto = GenericFeatureStatisticsGenerator().ProtoFromDataFrames(
            datasets
        )
        protostr = base64.b64encode(proto.SerializeToString()).decode("utf-8")

        template = os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "stats.html"
        )
        html_template = path_utils.read_file_contents_as_string(template)

        h = html_template.replace("protostr", protostr)
        return h

    def generate_facet(self, h: str, magic: bool = False) -> None:
        """Generate a Facet Overview

        Args:
            h: HTML represented as a string.
            magic: Whether to magically materialize facet in a notebook.
        """
        if magic:
            if "ipykernel" not in sys.modules:
                raise EnvironmentError(
                    "The magic functions are only usable in a Jupyter notebook."
                )
            display(HTML(h))
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
                path_utils.write_file_contents_as_string(f.name, h)
                url = f"file:///{f.name}"
                webbrowser.open(url, new=2)
