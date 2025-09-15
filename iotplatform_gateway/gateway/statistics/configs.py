

from iotplatform_gateway.gateway.statistics.service_functions import StatisticsServiceFunctions

ONCE_SEND_STATISTICS_CONFIG = [
    {
        "function": StatisticsServiceFunctions.total_memory,
        "attributeOnGateway": "totalMemory"
    },
    {
        "function": StatisticsServiceFunctions.total_disk_memory,
        "attributeOnGateway": "totalDisk"
    },
    {
        "function": StatisticsServiceFunctions.total_cpu_count,
        "attributeOnGateway": "cpuCount"
    }
]

SERVICE_STATS_CONFIG = [
    {
        "function": StatisticsServiceFunctions.storage_msgs_pulled,
        "attributeOnGateway": "storageMsgPulled"
    },
    {
        "function": StatisticsServiceFunctions.storage_msgs_count,
        "attributeOnGateway": "storageMsgCount"
    },
    {
        "function": StatisticsServiceFunctions.platform_msgs_pushed,
        "attributeOnGateway": "platformMsgPushed"
    },
    {
        "function": StatisticsServiceFunctions.platform_attr_produced,
        "attributeOnGateway": "platformAttrProduced"
    },
    {
        "function": StatisticsServiceFunctions.platform_ts_produced,
        "attributeOnGateway": "platformTsProduced"
    }
]

MACHINE_STATS_CONFIG = [
    {
        "function": StatisticsServiceFunctions.cpu_usage,
        "attributeOnGateway": "totalCpuUsage"
    },
    {
        "function": StatisticsServiceFunctions.disk_usage_perc,
        "attributeOnGateway": "diskUsage"
    },
    {
        "function": StatisticsServiceFunctions.ram_usage,
        "attributeOnGateway": "freeMemory"
    },
    {
        "function": StatisticsServiceFunctions.free_disk_space,
        "attributeOnGateway": "freeDisk"
    },
    {
        "function": StatisticsServiceFunctions.gateway_cpu_usage,
        "attributeOnGateway": "gwProcessCpuUsage"
    },
    {
        "function": StatisticsServiceFunctions.gateway_process_memory_usage_percent,
        "attributeOnGateway": "gwMemory"
    },
    {
        "function": StatisticsServiceFunctions.gateway_process_memory_full_info,
        "attributeOnGateway": "gwProcessMemoryFullInfo"
    },
    {
        "function": StatisticsServiceFunctions.msgs_sent_to_platform,
        "attributeOnGateway": "msgsSentToPlatform"
    },
    {
        "function": StatisticsServiceFunctions.msgs_received_from_platform,
        "attributeOnGateway": "msgsReceivedFromPlatform"
    }
]
