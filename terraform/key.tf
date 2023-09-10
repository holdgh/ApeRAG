resource "aws_key_pair" "ssh_key" {
  key_name   = "yunjia"
  public_key = file("~/.ssh/id_rsa.pub")
}
