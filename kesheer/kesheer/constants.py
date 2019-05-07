# -- coding: utf-8 --

# 图片验证码的redis有效期 单位：秒
IMAGE_CODE_REDIS_EXPIRES = 180

# 短信验证码的redis有效期 单位：秒
SMS_CODE_REDIS_EXPIRES = 300

# 发送短信验证码的间隔 单位：秒
SEND_SMS_CODE_REDIS_INTERVAL = 60

# 登录错误尝试次数
LOGIN_ERROR_MAX_TIMES = 5

# 登录错误限制时间， 单位：秒
LOGIN_ERROR_FORBID_TIMES = 600

# 七牛的域名
QINIU_URL_DOMIN = "http://pk111lso2.bkt.clouddn.com/"

# 城区信息的缓存时间，单位：秒
AREA_INFO_REDIS_CACHE_EXPIRES = 7200

# 首页最多展示房屋数量
HOME_PAGE_MAX_HOUSES = 5

# 首页房屋数据的Redis缓存时间，单位：秒
HOUSE_PAGE_DATA_REDIS_EXPIRES = 7200

# 房屋详情页面展示的最大评论数
HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS = 30

# 房屋详情页面数据Redis缓存时间，单位：秒
HOUSE_DETAIL_REDIS_EXPIRE_SECOND = 7200

# 房屋列表页每页数据容量
HOUSE_LIST_PAGE_CAPACITY = 6

# 房屋列表页面页数缓存时间：单位s
HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES = 7200
