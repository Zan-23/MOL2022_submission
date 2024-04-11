
import dash
import dash_bootstrap_components as dbc
import sys

from src.dashboard.layout_creation import load_app
from src.jpred_queries import submit_job_and_retrieve_results


def run_jpred_main():
    submit_job_and_retrieve_results(
        sequence="MQVWPIEGIKKFETLSYLPPLTVEDLLKQIEYLLRSKWVPCLEFSKVGFVYRENHRSPGYYDGRYWTMWKLPMFGCTDATQVLKELEEAKKAYPDAFVRIIGFDNVRQVQLISFIAYKPPGC")


if __name__ == "__main__":
    # this need to be set for build/deploy
    sys.stdout.reconfigure(encoding='utf-8')

    # suppress_callback_exceptions is used to suppress the error message of callbacks on elements
    print(f"Starting app...")
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CERULEAN], suppress_callback_exceptions=True)
    app.title = "Jpred Advanced Visualizer"

    # Start the program
    load_app(app)
    app.run_server(debug=True, port=8051)
