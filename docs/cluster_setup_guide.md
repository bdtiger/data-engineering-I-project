# Cluster Setup Guide — Data Engineering I (Group 32)

> **Course:** 1TD169 Data Engineering I, Uppsala University VT 2026  
> **Cluster:** 1 Master + 3 Workers on OpenStack SSC  
> **Stack:** Java 11 · Hadoop 3.4.1 · Spark 3.5.1 · PySpark 3.5.1

---

## Cluster Overview

| Node | Hostname | Internal IP | Public IP |
|------|----------|-------------|-----------|
| Master | `group-32-master` | `192.168.2.137` | `130.238.27.251` |
| Worker 1 | `group-32-worker-1` | `192.168.2.242` | — |
| Worker 2 | `group-32-worker-2` | TBD | — |
| Worker 3 | `group-32-worker-3` | TBD | — |

> Workers have no Floating IP — accessible only from Master via internal network.

**Setup strategy:** Fully configure Master → take OpenStack snapshot (`group-32-cluster-base`) → clone Workers from snapshot → set hostnames and IPs on each Worker.

---

## Part 1: Master Node Setup

All steps in Part 1 are performed **on the Master node** via SSH:

```bash
ssh -i ~/.ssh/de1-course-snic-key.pem ubuntu@130.238.27.251
```

---

### Step 1.1: Install Java (OpenJDK 11)

Hadoop and Spark both require Java 11.

```bash
sudo apt update
sudo apt install openjdk-11-jdk-headless net-tools -y
```

Verify:

```bash
java -version
javac -version
# Expected: openjdk version "11.0.x"
```

---

### Step 1.2: Set JAVA_HOME

**System-wide** (required by Hadoop daemons started as services):

```bash
sudo vim /etc/environment
```

Add this line:

```
JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64/
```

Save and exit, then apply to the current session:

```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64/
```

Verify:

```bash
echo $JAVA_HOME
ls $JAVA_HOME/bin/java
```

---

### Step 1.3: Update `/etc/hosts`

Hadoop and Spark use hostnames (e.g. `group-32-master`) for inter-node communication. These must resolve correctly on all nodes before configuring Hadoop.

```bash
sudo vim /etc/hosts
```

Add entries for all cluster nodes:

```
127.0.0.1       localhost
192.168.2.137   group-32-master
192.168.2.242   group-32-worker-1
<worker-2-ip>   group-32-worker-2
<worker-3-ip>   group-32-worker-3
```

> Replace `<worker-2-ip>` and `<worker-3-ip>` with actual IPs once those VMs are created. Worker IPs are visible in the OpenStack dashboard.

Verify hostname resolution:

```bash
ping -c 1 group-32-master
```

---

### Step 1.4: Install Hadoop 3.4.1

```bash
cd ~
wget https://dlcdn.apache.org/hadoop/common/hadoop-3.4.1/hadoop-3.4.1.tar.gz
tar -xzf hadoop-3.4.1.tar.gz
rm hadoop-3.4.1.tar.gz
```

> Download is ~600 MB. Extraction takes a few minutes.

Verify:

```bash
./hadoop-3.4.1/bin/hadoop version
```

Add Hadoop to PATH in `~/.bashrc`:

```bash
echo 'export HADOOP_HOME=~/hadoop-3.4.1' >> ~/.bashrc
echo 'export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin' >> ~/.bashrc
echo 'export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64/' >> ~/.bashrc
source ~/.bashrc
```

---

### Step 1.5: Configure Hadoop

All config files are in `~/hadoop-3.4.1/etc/hadoop/`.

#### `core-site.xml` — HDFS address

```bash
vim ~/hadoop-3.4.1/etc/hadoop/core-site.xml
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://group-32-master:9000</value>
  </property>
</configuration>
```

#### `hdfs-site.xml` — Replication and data directories

```bash
vim ~/hadoop-3.4.1/etc/hadoop/hdfs-site.xml
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <property>
    <name>dfs.replication</name>
    <value>1</value>
  </property>
  <property>
    <name>dfs.namenode.name.dir</name>
    <value>file:///home/ubuntu/hadoop-data/namenode</value>
  </property>
  <property>
    <name>dfs.datanode.data.dir</name>
    <value>file:///home/ubuntu/hadoop-data/datanode</value>
  </property>
</configuration>
```

> **Note:** Replication is set to `1` initially. Change to `2` once all 3 Workers are active.

Create the data directories:

```bash
mkdir -p ~/hadoop-data/namenode ~/hadoop-data/datanode
```

#### `yarn-site.xml` — YARN ResourceManager

```bash
vim ~/hadoop-3.4.1/etc/hadoop/yarn-site.xml
```

```xml
<?xml version="1.0"?>
<configuration>
  <property>
    <name>yarn.nodemanager.aux-services</name>
    <value>mapreduce_shuffle</value>
  </property>
  <property>
    <name>yarn.resourcemanager.hostname</name>
    <value>group-32-master</value>
  </property>
</configuration>
```

#### `mapred-site.xml` — MapReduce framework

```bash
vim ~/hadoop-3.4.1/etc/hadoop/mapred-site.xml
```

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <property>
    <name>mapreduce.framework.name</name>
    <value>yarn</value>
  </property>
</configuration>
```

#### `workers` — Hadoop worker nodes

```bash
vim ~/hadoop-3.4.1/etc/hadoop/workers
```

```
group-32-worker-1
```

> Add `group-32-worker-2` and `group-32-worker-3` here when those nodes are ready.

#### `hadoop-env.sh` — JAVA_HOME for Hadoop daemons

```bash
echo 'export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64/' >> ~/hadoop-3.4.1/etc/hadoop/hadoop-env.sh
```

---

### Step 1.6: Configure SSH Key-Based Access

Hadoop and Spark use SSH to start/stop daemons on worker nodes. The Master needs passwordless SSH to all Workers.

```bash
ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

> When Workers are created from the snapshot, this public key is already present in their `authorized_keys`. No further action needed on Workers for SSH.

---

### Step 1.7: Install Spark 3.5.1

```bash
cd ~
wget https://archive.apache.org/dist/spark/spark-3.5.1/spark-3.5.1-bin-hadoop3.tgz
tar -xzf spark-3.5.1-bin-hadoop3.tgz
rm spark-3.5.1-bin-hadoop3.tgz
mv spark-3.5.1-bin-hadoop3 spark
```

Add Spark to PATH in `~/.bashrc`:

```bash
echo 'export SPARK_HOME=~/spark' >> ~/.bashrc
echo 'export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin' >> ~/.bashrc
source ~/.bashrc
```

---

### Step 1.8: Configure Spark

#### `spark-env.sh`

```bash
cp ~/spark/conf/spark-env.sh.template ~/spark/conf/spark-env.sh
cat >> ~/spark/conf/spark-env.sh <<'EOF'
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64/
export HADOOP_CONF_DIR=~/hadoop-3.4.1/etc/hadoop
export SPARK_MASTER_HOST=group-32-master
EOF
```

#### `workers` — Spark worker nodes

```bash
vim ~/spark/conf/workers
```

```
group-32-worker-1
```

> Add `group-32-worker-2` and `group-32-worker-3` here when those nodes are ready.

---

### Step 1.9: Install PySpark

```bash
sudo apt install python3-pip -y
pip3 install pyspark==3.5.1
```

---

### Step 1.10: Take OpenStack Snapshot

Before launching Workers, take a snapshot of the fully configured Master:

1. In the OpenStack dashboard, go to **Compute → Instances**
2. Select the Master instance → **Create Snapshot**
3. Name it: `group-32-cluster-base`

This snapshot is used to create all Worker VMs — they inherit the full software stack.

---

## Part 2: Worker Node Setup

Each Worker is created from the `group-32-cluster-base` snapshot. The following steps are done **per Worker after launch**.

---

### Step 2.1: Set Hostname

SSH into each Worker from the Master and set its hostname:

```bash
# On Worker 1:
sudo hostnamectl set-hostname group-32-worker-1

# On Worker 2:
sudo hostnamectl set-hostname group-32-worker-2

# On Worker 3:
sudo hostnamectl set-hostname group-32-worker-3
```

Log out and back in for the hostname to take effect.

---

### Step 2.2: Update `/etc/hosts` on All Nodes

Get each Worker's internal IP from the OpenStack dashboard, then update `/etc/hosts` on **every node** (Master and all Workers).

```bash
sudo vim /etc/hosts
```

Final `/etc/hosts` (all nodes):

```
127.0.0.1       localhost
192.168.2.137   group-32-master
192.168.2.242   group-32-worker-1
<worker-2-ip>   group-32-worker-2
<worker-3-ip>   group-32-worker-3
```

---

### Step 2.3: Verify SSH from Master to Workers

```bash
ssh ubuntu@group-32-worker-1 hostname   # should print: group-32-worker-1
ssh ubuntu@group-32-worker-2 hostname   # should print: group-32-worker-2
ssh ubuntu@group-32-worker-3 hostname   # should print: group-32-worker-3
```

---

## Part 3: Starting the Cluster

All start commands are run **on the Master node**.

---

### Step 3.1: Format the NameNode (First Time Only)

> **Run this exactly once.** Re-formatting destroys all HDFS data.

```bash
hdfs namenode -format
```

---

### Step 3.2: Start HDFS

```bash
start-dfs.sh
```

Verify on Master:

```bash
jps
# Expected: NameNode, SecondaryNameNode
```

Verify DataNodes are live:

```bash
hdfs dfsadmin -report | grep "Live datanodes"
# Expected: Live datanodes (1)  ← increases as workers are added
```

---

### Step 3.3: Start YARN

```bash
start-yarn.sh
```

Verify on Master:

```bash
jps
# Expected: NameNode, SecondaryNameNode, ResourceManager
```

Verify Worker (from Master):

```bash
ssh ubuntu@group-32-worker-1 jps
# Expected: DataNode, NodeManager
```

---

### Step 3.4: Start Spark

```bash
start-master.sh
start-workers.sh
```

Verify Master:

```bash
jps
# Expected: NameNode, SecondaryNameNode, ResourceManager, Master
```

Verify Worker:

```bash
ssh ubuntu@group-32-worker-1 jps
# Expected: DataNode, NodeManager, Worker
```

---

### Step 3.5: End-to-End Smoke Test

```bash
spark-submit --master spark://group-32-master:7077 \
  /home/ubuntu/spark/examples/src/main/python/pi.py 10
```

Expected output contains:

```
Pi is roughly 3.14...
```

---

## Part 4: Web UIs

Access cluster dashboards by SSH tunneling from your local machine:

```bash
ssh -i ~/.ssh/de1-course-snic-key.pem \
    -L 8888:localhost:8888 \
    -L 4040:localhost:4040 \
    -L 4041:localhost:4041 \
    -L 4042:localhost:4042 \
    -L 8080:localhost:8080 \
    -L 9870:localhost:9870 \
    ubuntu@130.238.27.251
```

Then open in your browser:

| UI | URL | Description |
|----|-----|-------------|
| Spark Master | http://localhost:8080 | Workers, running/completed apps |
| HDFS NameNode | http://localhost:9870 | Filesystem browser, DataNode status |
| Spark App UI | http://localhost:4040 | Jobs, stages, executors (during job run) |
| Jupyter | http://localhost:8888 | Notebooks (once Jupyter is started on Master) |

---

## Part 5: Stopping the Cluster

```bash
stop-workers.sh
stop-master.sh
stop-yarn.sh
stop-dfs.sh
```

---

## Part 6: Adding Workers 2 and 3

Once Workers 2 and 3 are ready:

1. Update `/etc/hosts` on all 4 nodes with the new IPs
2. Add to Hadoop workers file on Master:
   ```bash
   echo 'group-32-worker-2' >> ~/hadoop-3.4.1/etc/hadoop/workers
   echo 'group-32-worker-3' >> ~/hadoop-3.4.1/etc/hadoop/workers
   ```
3. Add to Spark workers file on Master:
   ```bash
   echo 'group-32-worker-2' >> ~/spark/conf/workers
   echo 'group-32-worker-3' >> ~/spark/conf/workers
   ```
4. Change HDFS replication from `1` to `2` in `hdfs-site.xml`:
   ```xml
   <property>
     <name>dfs.replication</name>
     <value>2</value>
   </property>
   ```
5. Restart the cluster (Steps 3.2–3.4)
6. Apply the new replication factor to existing data:
   ```bash
   hdfs dfs -setrep -R 2 /
   ```

---

## Quick Reference

### Process Overview per Node

| Process | Node | Service |
|---------|------|---------|
| `NameNode` | Master | HDFS metadata |
| `SecondaryNameNode` | Master | HDFS checkpointing |
| `ResourceManager` | Master | YARN resource management |
| `Master` | Master | Spark standalone master |
| `DataNode` | Each Worker | HDFS data storage |
| `NodeManager` | Each Worker | YARN task execution |
| `Worker` | Each Worker | Spark standalone worker |

### Key Paths

| Component | Path |
|-----------|------|
| Hadoop home | `~/hadoop-3.4.1/` |
| Hadoop config | `~/hadoop-3.4.1/etc/hadoop/` |
| Hadoop data | `~/hadoop-data/` |
| Spark home | `~/spark/` |
| Spark config | `~/spark/conf/` |
| Spark logs | `~/spark/logs/` |
| SSH key | `~/.ssh/id_rsa` |
