import json
import csv
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

def parse_har_file(har_file):
    har_data = json.load(har_file)
    return har_data

def analyze_har_data(har_data, threshold_time_total, threshold_time_single_call):
    url_data = {}
    
    for entry in har_data['log']['entries']:
        url = entry['request']['url']
        time_taken = entry['time']
        start_time = datetime.strptime(entry['startedDateTime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        end_time = start_time + timedelta(milliseconds=time_taken)

        if url not in url_data:
            url_data[url] = {
                'total_time': 0,
                'max_time': 0,
                'call_count': 0,
                'parallel_calls': []
            }

        url_data[url]['total_time'] += time_taken
        url_data[url]['max_time'] = max(url_data[url]['max_time'], time_taken)
        url_data[url]['call_count'] += 1

        # Track parallel calls
        overlapping_calls = sum(1 for call in url_data[url]['parallel_calls'] if call['start_time'] < end_time and call['end_time'] > start_time)
        url_data[url]['parallel_calls'].append({
            'start_time': start_time,
            'end_time': end_time,
            'overlapping_calls': overlapping_calls
        })

    results = []
    for url, data in url_data.items():
        if data['total_time'] > threshold_time_total or data['max_time'] > threshold_time_single_call:
            max_parallel_calls = max(call['overlapping_calls'] for call in data['parallel_calls']) + 1
            results.append({
                'URL': url,
                'Total Time': data['total_time'],
                'Max Time for a Single Call': data['max_time'],
                'Number of Calls': data['call_count']
            })
    
    return results

def write_report_to_csv(results):
    df = pd.DataFrame(results)
    return df.to_csv(index=False).encode('utf-8')

def main():
    st.title("HAR File Analysis")

    uploaded_file = st.file_uploader("Upload HAR File", type=["har"])
    threshold_time_total = st.number_input("Threshold for Total Time (in ms)", min_value=0.0, value=5000.0)
    threshold_time_single_call = st.number_input("Threshold for Single Call Time (in ms)", min_value=0.0, value=300.0)

    if uploaded_file is not None:
        har_data = parse_har_file(uploaded_file)
        results = analyze_har_data(har_data, threshold_time_total, threshold_time_single_call)
        
        if results:
            st.write("URLs that exceed the thresholds:")
            st.dataframe(results)

            csv = write_report_to_csv(results)
            st.download_button(
                label="Download CSV Report",
                data=csv,
                file_name='har_report.csv',
                mime='text/csv',
            )
        else:
            st.write("No URLs exceeded the provided thresholds.")

if __name__ == '__main__':
    main()
