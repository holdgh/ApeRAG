```bash
kbcli cluster describe mysql-cluster

Name: mysql-cluster	 Created Time: Apr 23,2023 15:50 UTC+0800
NAMESPACE   CLUSTER-DEFINITION   VERSION           STATUS    TERMINATION-POLICY
default     apecloud-mysql       ac-mysql-8.0.30   Running   Delete

Endpoints:
COMPONENT   MODE        INTERNAL                                             EXTERNAL
mysql       ReadWrite   mysql-cluster-mysql.default.svc.cluster.local:3306   <none>

Topology:
COMPONENT   INSTANCE                ROLE       STATUS    AZ                NODE                                                             CREATED-TIME
mysql       mysql-cluster-mysql-0   leader     Running   cn-northwest-1c   ip-172-31-39-93.cn-northwest-1.compute.internal/172.31.39.93     Apr 23,2023 15:50 UTC+0800
mysql       mysql-cluster-mysql-1   follower   Running   cn-northwest-1b   ip-172-31-28-145.cn-northwest-1.compute.internal/172.31.28.145   Apr 23,2023 15:50 UTC+0800
mysql       mysql-cluster-mysql-2   follower   Running   cn-northwest-1a   ip-172-31-7-150.cn-northwest-1.compute.internal/172.31.7.150     Apr 23,2023 15:50 UTC+0800

Resources Allocation:
COMPONENT   DEDICATED   CPU(REQUEST/LIMIT)   MEMORY(REQUEST/LIMIT)   STORAGE-SIZE   STORAGE-CLASS
mysql       false       1 / 1                1Gi / 1Gi               data:20Gi      ebs-sc

Images:
COMPONENT   TYPE    IMAGE
mysql       mysql   registry.cn-hangzhou.aliyuncs.com/apecloud/apecloud-mysql-server:8.0.30-5.alpha5.20230319.g28f261a.5

Data Protection:
AUTO-BACKUP   BACKUP-SCHEDULE   TYPE       BACKUP-TTL   LAST-SCHEDULE   RECOVERABLE-TIME
Disabled      0 18 * * 0        snapshot   7d           <none>          <none>

Events(last 5 warnings, see more:kbcli cluster list-events -n default mysql-cluster):
TIME                         TYPE      REASON        OBJECT                           MESSAGE
Apr 23,2023 15:50 UTC+0800   Warning   FailedMount   Instance/mysql-cluster-mysql-2   MountVolume.SetUp failed for volume "scripts" : failed to sync configmap cache: timed out waiting for the condition
```
