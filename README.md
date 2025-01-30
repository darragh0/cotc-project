# 'Content of the Code' Project

### Functional Requirements

-   System-monitoring tool that provides cloud dashboards for PC & 3rd party device status & history
    -   At least 2 devices
    -   At least 2 metrics per device (e.g. running threads, open processes, RAM usage)
    -   Choose values that change regularly (but not at sub-second frequency)
-   Gather information from PC & then 3rd party service/device
    -   3rd party → e.g. cloud weather service, IOT device, stock price
-   Report that info. to a cloud based service
-   Store a history of info. on the cloud server
-   Present a dashboard UI showing live/historic data
-   Stretch goal – send messages back to the device (e.g. restart app)

### Non-Functional Requirements

-   Understand the **why** behind every interface/component built
-   Flexible data flow so new services/devices & metrics can be added over time w/o massive rework
-   Understand every line of code in detail
