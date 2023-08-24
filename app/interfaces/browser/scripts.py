"""используемые java-скрипты"""

service_data_script = """
            let plate = document.createElement("div");
            plate.innerHTML = `
                <div style="
                    max-width: 600px;
                    padding: 10px; margin: 0;
                    position: fixed; top: 20px; left: 20px;
                    color: white; font-size: 14px; font-family: monospace;
                    background-color:rgba(0, 0, 0, 0.8);
                    z-index: 2147483647;">
                    {datestring}<br>
                    {url}
                </div>
            `;
            document.body.appendChild(plate);"""

scrolling_page_script = """let h = document.body.scrollHeight;
 window.scrollTo({{{direction}: {offset}, behavior:"smooth"}});"""

scroll_to_element_script = """let h = Math.max(document.documentElement.clientHeight,
                            window.innerHeight || 0);
                          let el = arguments[0].getBoundingClientRect().top;
                          window.scrollBy(0, el-(h/2));"""

get_height_of_content = """return Math.max(
    document.scrollingElement.scrollHeight,
    document.body.scrollHeight,
)
"""

get_max_height_any_element = """return Math.max(
    ...[
            ...document.querySelectorAll('*')
        ].map(e => e.scrollHeight)
)
"""
