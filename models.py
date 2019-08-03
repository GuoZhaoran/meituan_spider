from peewee import *

# 连接数据库
db = MySQLDatabase("meituan_spider", host="127.0.0.1", port=3306, user="root", password="root", charset="utf8")


class BaseModel(Model):
    class Meta:
        database = db


# 商家表，用来存放商家信息
class Merchant(BaseModel):
    id = AutoField(primary_key=True, verbose_name="商家id")
    name = CharField(max_length=255, verbose_name="商家名称")
    address = CharField(max_length=255, verbose_name="商家地址")
    website_address = CharField(max_length=255, verbose_name="网络地址")
    website_address_hash = CharField(max_length=32, verbose_name="网络地址的md5值，为了快速索引")
    mobile = CharField(max_length=32, verbose_name="商家电话")
    business_hours = CharField(max_length=255, verbose_name="营业时间")


# 商家推荐菜表，存放菜品的推荐信息
class Recommended_dish(BaseModel):
    merchant_id = ForeignKeyField(Merchant, verbose_name="商家外键")
    name = CharField(max_length=255, verbose_name="推荐菜名称")


# 用户评价表，存放用户的评论信息
class Evaluate(BaseModel):
    id = CharField(primary_key=True)
    merchant_id = ForeignKeyField(Merchant, verbose_name="商家外键")
    user_name = CharField(verbose_name="用户名")
    evaluate_time = DateTimeField(verbose_name="评价时间")
    content = TextField(default="", verbose_name="评论内容")
    star = IntegerField(default=0, verbose_name="评分")
    image_list = TextField(default="", verbose_name="图片")


if __name__ == "__main__":
    db.create_tables([Merchant, Recommended_dish, Evaluate])
