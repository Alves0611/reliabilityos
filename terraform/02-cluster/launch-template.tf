resource "aws_launch_template" "node_group" {
  name_prefix = "${var.cluster_name}-node-"

  user_data = base64encode(<<-USERDATA
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="==MYBOUNDARY=="

--==MYBOUNDARY==
Content-Type: text/x-shellscript; charset="us-ascii"

#!/bin/bash
/etc/eks/bootstrap.sh ${var.cluster_name} --use-max-pods false --kubelet-extra-args '--max-pods=110'

--==MYBOUNDARY==--
USERDATA
  )

  tags = var.tags
}
