import os

from dash import html,  dcc, Output, Input, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import src.dashboard.web_config as conf
from src.jpred_queries import submit_job_and_retrieve_results, load_jal_view

import dash_bio as dashbio


def load_app(app):
    app.layout = dbc.Container([
        html.H1("Jpred4 Advanced visualization", style={"textAlign": "center"}),
        html.H6("A Protein Secondary Structure Prediction Server", style={"textAlign": "center"}),
        html.Div(children=[
            html.Label("Input sequence:"),
            dcc.Textarea(id=conf.SEQUENCE_INPUT_TEXTAREA, value="MQVWPIEGIKKFETLSYLPP",
                          style={"width": "100%", "height": "100px", "border-radius": "10px"}),
            html.Button("Submit", id=conf.SUBMIT_JOB_BTN, n_clicks=0, style={"border-radius": "10px"})
        ]),
        dcc.Loading(
            id="loading-2",
            children=[html.Div(id=conf.ALIGNMENT_CHART_DIV, children=[])],
            type="circle",
            style={"marginTop": "25px"}
        ),
        html.Div(children=[]),
        dcc.Store(id=conf.JOB_ID_STORE, data=[], storage_type="memory")
    ],
        style={"paddingLeft": "20px", "paddingRight": "20px"})

    # add callbacks
    add_callbacks_to_app(app)


def filter_out_content(data: str):
    assert "JNETSOL0" in data, "JNETSOL0 not found in the file"
    assert "JNETSOL5" in data, "JNETSOL5 not found in the file"
    assert "JNETSOL25" in data, "JNETSOL25 not found in the file"
    assert "Lupas_21" in data, "jnetpred not found in the file"
    split_data = data.split("\n")

    jnet_pred_line = None
    for line_num, line in enumerate(split_data):
        if "Lupas_21" in line:
            jnet_pred_line = line_num
            print(f"Lupas_21 found at line: {line_num}")
            break

    if jnet_pred_line < 45:
        print("Lupas_21 line is too low, returning all data")
        return data
    else:
        higher_data = data.split(">")[:16]
        higher_data = ">".join(higher_data)
        after_jnet_pred = "\n".join(split_data[jnet_pred_line:])
        filtered_data = higher_data + after_jnet_pred
        return filtered_data


def add_callbacks_to_app(app):
    @app.callback([Output(conf.ALIGNMENT_CHART_DIV, "children"),
                   Output(component_id=conf.JOB_ID_STORE, component_property="data")],
                    [Input(conf.SUBMIT_JOB_BTN, "n_clicks")],
                     State(conf.SEQUENCE_INPUT_TEXTAREA, "value"))
    def update_alignment_chart_on_btn_submit(n_clicks, textarea_content):
        print("Updating alignment chart ...")

        if n_clicks < 1 or textarea_content is None or len(textarea_content.strip()) < 1:
            return [html.Div()], {}
        sequence = textarea_content.strip()
        job_id, saved_path = submit_job_and_retrieve_results(sequence=sequence)
        # saved_path = "jpred_files/query_results/"
        # job_id = "jp_NZvGbY9"
        folder_path = f"{saved_path}/{job_id}"

        # sometimes the files don't share the job names, so we have to find them
        concise_fasta_file = [path for path in os.listdir(folder_path) if ".concise.fasta" in path]
        assert len(concise_fasta_file) == 1, f"Expected 1 concise fasta file, got {len(concise_fasta_file)}"
        concise_fasta_file = concise_fasta_file[0]

        with open(f"{folder_path}/{concise_fasta_file}", "r") as file:
            data = file.read()
        assert data.count(">") >= 2, "At least two data entries should be returned, nothing found!"
        data = filter_out_content(data)
        most_relevant_seq = data.split(">")[2].split("\n")[0]
        uniprot_link = f"https://www.uniprot.org/uniref/{most_relevant_seq}"

        # get jpred confidence
        jconf_file = [path for path in os.listdir(folder_path) if ".jalview" in path]
        assert len(jconf_file) == 1, f"Expected 1 jalview file, got {len(jconf_file)}"
        jconf_file = jconf_file[0]
        conf_data = load_jal_view(f"{folder_path}/{jconf_file}")

        conf_barchart = go.Figure(data=[go.Bar(x=[i[0] for i in conf_data], y=[i[1] for i in conf_data])])
        conf_barchart.update_layout(title="JNETCONF", height=300, xaxis_title="Position", yaxis_title="Confidence")

        alignment_chart = dashbio.AlignmentChart(
            id=conf.ALIGNMENT_CHART_ID,
            data=data,
            tilewidth=30,
            tileheight=30,
            width=1200,
            showconservation=True,
            showgap=False
        )

        return [html.Div(children=[
            html.Div(children=[
                html.H5(),
                html.Label(f"Job ID: {job_id}")
            ], style={"marginTop": "20px"}),
            html.Div(children=[
                html.Label(f"Sequence length: {len(sequence)}"),
                html.Br(),
                html.Label(["Most relevant sequence: ", html.A(uniprot_link, href=uniprot_link, target="_blank")])
            ], style={"marginTop": "20px"}),
            dcc.Graph(figure=conf_barchart),
            html.H3(f"Alignment chart for sequence:"),
            html.Label(f"{sequence}", style={"overflow-wrap": "break-word", "color": "black"}),
            alignment_chart])
        ],  {"job_id": job_id}