variable "repositories" { type = list(string) }

resource "aws_ecr_repository" "repos" {
  for_each = toset(var.repositories)
  name                 = each.value
  image_tag_mutability = "MUTABLE"
  force_delete         = true
}
