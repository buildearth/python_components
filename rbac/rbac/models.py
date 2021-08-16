from django.db import models


class Menu(models.Model):
    """
    一级菜单表
    """
    title = models.CharField(verbose_name='一级菜单名称', max_length=32)
    icon = models.CharField(verbose_name="图标", max_length=32, null=True, blank=True)

    def __str__(self):
        return self.title


class Permission(models.Model):
    """
    权限表
    """
    title = models.CharField(verbose_name='标题', max_length=32)
    url = models.CharField(verbose_name='含正则的URL', max_length=128)
    name = models.CharField(verbose_name='URL的别名', max_length=32, unique=True)

    menu = models.ForeignKey(to="Menu", verbose_name="所属菜单", null=True, blank=True, help_text="null表示不是菜单，非null表示是二级菜单")
    pid = models.ForeignKey(verbose_name="关联的权限",
                            help_text="对于非菜单权限选择一个可以成为菜单的权限，用于做默认展开和选中在访问非菜单功能时",
                            to="Permission",
                            null=True,
                            blank=True,
                            related_name="parents")

    def __str__(self):
        return self.title



class Role(models.Model):
    """
    角色
    """
    title = models.CharField(verbose_name='角色名称', max_length=32)
    permissions = models.ManyToManyField(verbose_name='拥有的所有权限', to='Permission', blank=True)

    def __str__(self):
        return self.title


class UserInfo(models.Model):
    """
    用户表
    """
    name = models.CharField(verbose_name='用户名', max_length=32)
    password = models.CharField(verbose_name='密码', max_length=64)
    email = models.CharField(verbose_name='邮箱', max_length=32)
    roles = models.ManyToManyField(verbose_name='拥有的所有角色', to=Role, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        # django以后再做数据库迁移时，不再为UserInfo类创建相关的表以及表结构了。
        # 此类可以当做"父类"，被其他Model类继承。
        abstract = True
