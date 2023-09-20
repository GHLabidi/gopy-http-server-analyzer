import json
import sys
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from plotly.subplots import make_subplots

class Analyzer:

    # data_path: path to the data file
    data_path = None
    server_url = None
    test_start_time = None
    title = ''
    description = ''
    concurrent_requests = None
    test_duration = None
    total_requests = None
    successful_requests = None
    failed_requests = None
    requests_per_second = None
    df = None
    meta = None
    graphs = []
    def __init__(self, test_unique_name):
        self.data_path = './performance_tests/' + test_unique_name + '/'
        # read meta data
        meta = json.load(open(self.data_path + 'metadata.json'))
        self.server_url = meta['server_url']
        # get test start time and convert it to datetime
        self.test_start_time = pd.to_datetime(meta['test_start_time'], unit='ns')
        # convert to readable format YYYY-MM-DD HH:MM:SS
        self.test_start_time = self.test_start_time.strftime("%Y-%m-%d %H:%M:%S")
        # extract test information
        self.title = meta['test_display_name']
        self.description = meta['test_description']
        self.concurrent_requests = meta['concurrent_requests']
        self.test_duration = meta['test_duration']
        self.total_requests = meta['total_requests']
        self.successful_requests = meta['successful_requests']
        self.failed_requests = meta['failed_requests']
        self.requests_per_second = meta['requests_per_second']
        
        
    def load_data(self):
        if self.total_requests is None or self.total_requests == 0:
            raise ValueError("Could not load data. Total requests is 0")
        # types
        data_types = {
            'IP': str,
            'Occurences': int,
            'LookupDuration': np.int64,
            'RequestDuration': np.int64,
            'StartTime': np.int64,  
            'EndTime': np.int64  
        }
        self.df = pd.read_csv(self.data_path+'data.csv', header=None, names=data_types.keys(), dtype=data_types)
        # setting datetime fields
        self.df['StartTime'] = pd.to_datetime(self.df['StartTime'], unit='ns')
        self.df['EndTime'] = pd.to_datetime(self.df['EndTime'], unit='ns')
        
    
    
    def analyze_latency(self, field_name, display_name, test_description = ''):
        if self.df is None:
            raise ValueError("The data was not loaded")
        
        
        # Analyze Mean Latency Per Second
        ## copy df and aggregate 'field_name' per second
        df_resampled = self.df.copy()
        df_resampled.set_index('StartTime', inplace=True)
        df_resampled = df_resampled.resample('1S').agg({field_name: 'mean'})
        ## reset index to show seconds passed instead of StartTime which is datetime
        start_time = df_resampled.index.min()
        df_resampled['SecondsPassed'] = (df_resampled.index - start_time).total_seconds()
        df_resampled.set_index('SecondsPassed', inplace=True)
        # convert nanoseconds to milliseconds
        df_resampled[field_name] = df_resampled[field_name] / 1000000
        
        
        # Analyze Summary Information
        ## copy df and extract 'field_name' column
        df_copy = self.df[field_name]
        ## get data description
        data_description = df_copy.describe().astype('int64')

        ## extract analysis    
        min = data_description['min']
        min_ip = self.df[self.df[field_name] == min]['IP'].iloc[0]
        min = min / 1000000 # convert to milliseconds

        mean = data_description['mean']
        mean = mean / 1000000 # convert to milliseconds

        std = data_description['std']
        std = std / 1000000 # convert to milliseconds

        max = data_description['max']
        max_ip = self.df[self.df[field_name] == max]['IP'].iloc[0]
        max = max / 1000000 # convert to milliseconds

        p25 = data_description['25%']
        p25 = p25 / 1000000 # convert to milliseconds

        p50 = data_description['50%']
        p50 = p50 / 1000000 # convert to milliseconds

        p75 = data_description['75%']
        p75 = p75 / 1000000 # convert to milliseconds
        
        ## html summary
        html_div = f"""
                    <div class='card rounded-xl m-10 p-10 border-2'>
                        <p class="text-lg font-bold italic">Summary Information</p>
                        <p class="italic">Mean Latency: <b>{mean}</b> milliseconds</p>
                        <p class="italic">Standard Deviation: <b>{std}</b> milliseconds</p>
                        <p class="italic">25th Percentile: <b>{p25}</b> milliseconds</p>
                        <p class="italic">50th Percentile: <b>{p50}</b> milliseconds</p>
                        <p class="italic">75th Percentile: <b>{p75}</b> milliseconds</p>
                        <p class="italic">Request with lowest latency: <b>{min}</b> milliseconds</p>
                        <p class="italic">IP address of the request with lowest latency: <b>{min_ip}</b></p>
                        <p class="italic">Request with highest latency: <b>{max}</b> milliseconds</p>
                        <p class="italic">IP address of the request with highest latency: <b>{max_ip}</b></p>
                    </div>
                    """

        
        # plotting the graphs
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Mean " + display_name +  " Per Second", "Summary Information"))
        # left figure
        fig.add_trace(go.Scatter(x=df_resampled.index, y=df_resampled[field_name],
                                mode='lines', name='Mean ' + display_name ),
                    row=1, col=1)
        fig.update_xaxes(title_text='Time (seconds)', row=1, col=1)
        fig.update_yaxes(title_text=display_name + '(ms)', row=1, col=1)

        # right figure
        fig.add_trace(go.Bar(x=['25%', '50%', '75%'], y=[p25, p50, p75],
                            text=[p25, p50, p75], textposition='outside',
                            
                            marker_color= ['blue', 'yellow', 'red'],
                            name='Summary Information'),
                    row=1, col=2)
        fig.update_xaxes(title_text='Statistic', row=1, col=2)
        fig.update_yaxes(title_text=display_name + '(ms)', row=1, col=2)

        # setup the layout for the subplots
        fig.update_layout(title_text=display_name + " Analysis", showlegend=False)
        fig.update_layout(height=500, width=1500)
        
        self.graphs.append({
            'title': display_name + " Analysis",
            'description': test_description,
            'html_summary': html_div,
            'fig': fig
        })
    def analyze_requests_per_second(self, test_description = ''):
        # copy and aggregate per second
        df_copy = self.df.copy()
        df_copy.set_index('StartTime', inplace=True)
        df_copy = df_copy.resample('1S').count()
        
        # reset index to show seconds passed instead of StartTime which is datetime
        start_time = df_copy.index.min()
        df_copy['SecondsPassed'] = (df_copy.index - start_time).total_seconds()
        df_copy.set_index('SecondsPassed', inplace=True)
        # rename columns and drop unnecessary ones
        df_copy.rename(columns={'IP': 'RequestsPerSecond'}, inplace=True)
        df_copy.drop(columns=['Occurences', 'LookupDuration', 'RequestDuration', 'EndTime'], inplace=True)
        # some stats. keeping only 2 decimal points
        mean = df_copy['RequestsPerSecond'].mean().__round__(2)
        std = df_copy['RequestsPerSecond'].std().__round__(2)
        max = df_copy['RequestsPerSecond'].max().__round__(2)
        min = df_copy['RequestsPerSecond'].min().__round__(2)

        # plotting the graph for requests per second
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_copy.index, y=df_copy['RequestsPerSecond'],
                                mode='lines', name='Requests Per Second'))
        fig.update_xaxes(title_text='Time (seconds)')
        fig.update_yaxes(title_text='Requests Per Second')

        # set the layout for the subplot
        fig.update_layout(title_text="Requests Per Second Analysis", showlegend=False)
        fig.update_layout(height=500, width=1500)

        # html summary
        html_div = f"""
                    <div class='card rounded-xl m-10 p-10 border-2'>
                        <p class="text-lg font-bold italic">Summary Information</p>
                        <p class="italic">Mean Requests Per Second: <b>{mean}</b> requests</p>
                        <p class="italic">Standard Deviation: <b>{std}</b> requests</p>
                        <p class="italic">Maximum Requests Per Second: <b>{max}</b> requests</p>
                        <p class="italic">Minimum Requests Per Second: <b>{min}</b> requests</p>
                    </div>
                    """
        self.graphs.append({
            'title': "Requests Per Second Analysis",
            'description': test_description,
            'html_summary': html_div,
            'fig': fig
        })

        



    def create_test_report_html(self):
        # create html file with the report data
        with open(self.data_path + 'report.html', 'w') as f:
            f.write("<html><head><title>" + self.title + "</title>")
            # use tailwind css
            f.write("<script src='https://cdn.tailwindcss.com'></script>")
            f.write("</head><body>")
            f.write("<div class='card rounded-xl m-10 p-10 border-2'>")
            f.write("<p class='text-2xl font-bold italic'>" + self.title + "</p>")
            f.write("<p class='text-lg font-bold italic'>Test Start Time: <b>" + self.test_start_time + "</b></p>")
            f.write("<p class='text-lg font-bold italic'>Server URL: <b>" + self.server_url + "</b></p>")
            f.write("<p class='text-lg font-bold italic'>Test Description:</p>")
            f.write("<p class='text-lg italic'>" + self.description + "</p>")
            f.write("<p class='font-bold italic'>Run Information:</p>")
            f.write("<p class='italic'>Concurrent Requests: <b>" + str(self.concurrent_requests) + "</b></p>")
            f.write("<p class='italic'>Test Duration: <b>" + str(self.test_duration) + "</b> seconds</p>")
            f.write("<p class='italic'>Total Requests: <b>" + str(self.total_requests) + "</b></p>")
            f.write("<p class='italic'>Successful Requests: <b>" + str(self.successful_requests) + "</b></p>")
            f.write("<p class='italic'>Failed Requests: <b>" + str(self.failed_requests) + "</b></p>")
            f.write("<p class='italic'>Average Requests Per Second (Total Requests / Test Duration): <b>" + str(self.requests_per_second) + "</b></p>")
            f.write("</div>")
            f.write("<hr class='!border-t-4'>")
            for graph in self.graphs:
                f.write("<div class='card rounded-xl m-10 p-10 border-2'>")
                f.write("<p class='text-xl font-bold italic'>" + graph['title'] + "</p>")
                if graph['description'] != '':
                    f.write("<div class='card justify-center rounded-xl m-10 p-10 border-2'>")
                    f.write("<p class='text-lg font-bold italic'> Test Description:</p>")
                    f.write("<p class='text-lg italic'>" + graph['description'] + "</p>")
                    f.write("</div>")
                f.write(graph['html_summary'])
                f.write("<div class='card flex justify-center rounded-xl m-10 p-10 border-2'>")
                f.write(graph['fig'].to_html(full_html=False, include_plotlyjs='cdn'))
                f.write("</div>")
                f.write("</div>") 
                
                f.write("<hr class='!border-t-4'>")


            f.write("</body></html>")
            f.close()

            print("Report created successfully")
            
    def generate_test_report_pdf(self):
        # create pdf file with the report data similar to the html file
        pass 
            





# main
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 generate_report.py <unique_test_name>")
        sys.exit(1)
    # create analyzer
    analyzer = Analyzer(sys.argv[1])
    # load data
    analyzer.load_data()
    # analyze requests per second
    test_description = """
                        This represents the number of requests processed by the server per second.
                        """
    analyzer.analyze_requests_per_second(test_description=test_description)
    # analyze lookup duration
    test_description = """
                        This represents the lookup duration of the client's ip in the server.
                        In this test, the server is storing the ip addresses in a hash table along with the number of requests made by this ip.
                        """
                        
    analyzer.analyze_latency('LookupDuration', 'Lookup Duration', test_description=test_description)
    # analyze request duration
    test_description = """
                        This represents the whole request duration from the moment the request is received by the server until the response is sent back to the client.
                        """
    analyzer.analyze_latency('RequestDuration', 'Request Duration', test_description=test_description)
    # create report
    analyzer.create_test_report_html()
