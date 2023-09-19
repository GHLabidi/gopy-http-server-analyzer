import os
import json
import time

tailwind_classes = {
    'card' : 'card rounded-xl border-2 p-10 m-10 flex justify-evenly items-center',
    'title' : 'text-center text-2xl font-bold m-4',
    'h2' : 'font-bold text-xl w-64',
    'flex-center-div' : 'flex justify-center',
    'link-button' : 'bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-full flex space-x-2',
    'main-div' : ''
}

def reindex():
    tests_dir = 'performance_tests'

    folder_list = []


    # sort folders by date 
    folders = os.listdir(tests_dir)
    folders.sort(key=lambda x: os.path.getmtime(os.path.join(tests_dir, x)), reverse=True)

    for folder_name in folders:
        test_path = os.path.join(tests_dir, folder_name)
        print(test_path)
        metadata_file = os.path.join(test_path, 'metadata.json')
        report_file = os.path.join(test_path, 'report.html')

        # verify that test is valid and files exist
        if os.path.isfile(metadata_file) and os.path.isfile(report_file):
            # read file
            with open(metadata_file, 'r') as metadata_json:
                metadata = json.load(metadata_json)
            # extract data
            server_url = metadata.get('server_url', 'N/A')
            test_start_time = metadata.get('test_start_time', 'N/A')
            #convert to human readable format
            test_start_time = test_start_time / 1000000000
            test_start_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(test_start_time))
            
            test_unique_name = metadata.get('test_unique_name', 'N/A')
            test_display_name = metadata.get('test_display_name', 'N/A')
            concurrent_requests = metadata.get('concurrent_requests', 'N/A')
            test_duration = metadata.get('test_duration', 'N/A')
            total_requests = metadata.get('total_requests', 'N/A')


            # link to report page
            report_link = f'''
                            
                            <a class="{tailwind_classes.get('link-button')}" href="./{folder_name}/report.html" target="_blank">
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-eye"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>

                                <p>View Full Report</p>
                            </a>
                            
                            '''

            folder_info = f'''
                            <div class="{tailwind_classes.get('card')}">
                                <p class="{tailwind_classes.get('h2')}">{test_display_name}</p>
                                <div class="space-y-2">
                                    <p>Server URL: {server_url}</p>
                                    <p>Test Start Time: {test_start_time}</p>
                                    <p>Concurrent Requests: {concurrent_requests}</p>
                                    <p>Test Duration: {test_duration} seconds</p>
                                </div>
                                <div class="{tailwind_classes.get('flex-center-div')}">
                                  {report_link}
                                </div>
                            </div>
                            '''
            folder_list.append(folder_info)
    index_html_content = f'''
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <title>Performance Tests</title>
                            <!-- Include Tailwind CSS as a CDN -->
                            <script src='https://cdn.tailwindcss.com'></script>
                        </head>
                        <body>
                            
                            <h1 class="{tailwind_classes.get('title')}">Performance Tests</h1>
                            <div class="{tailwind_classes.get('main-div')}">
                            {"".join(folder_list)}
                            </div>
                        </body>
                        </html>
                    '''
    index_file = os.path.join(tests_dir, 'index.html')
    with open(index_file, 'w') as file:
        file.write(index_html_content)
    print("Indexing complete")


if __name__ == '__main__':
    reindex()