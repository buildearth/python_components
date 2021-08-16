import re

from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import HttpResponse
from django.conf import settings


class RbacMiddleware(MiddlewareMixin):
    def process_request(self, request):
        '''
        1. 拿到当前用户请求的url
        2. 获取当前用户在session中保存的权限列表
        3. 权限信息匹配
        '''
        current_url = request.path_info
        # 有一些权限是所有人默认都有的，不需要做权限判断，先进行一个白名单判断，如果是白名单url，就不用再走权限判断了
        valid_url_list = settings.VALID_URL_LIST
        for valid_url in valid_url_list:
            if re.match(valid_url, current_url):
                # 白名单中的url，无需权限验证
                # 返回None，继续走后续步骤
                return None

        url_record = [
            {'title': '首页', 'url': '#'}
        ]

        for url in settings.NO_PERMISSION_LIST:
            if re.match(url, request.path_info):
                # 需要登录，但无需权限校验
                request.current_selected_permission = 0
                request.breadcrumb = url_record

                return None

        permission_dict = request.session.get(settings.PERMISSION_SESSION_KEY)
        if not permission_dict:
            # 返回 HttpResponse 不走 后续步骤，直接返回到页面
            return HttpResponse('为获取到用户权限信息')

        print(current_url)
        print(permission_dict)

        flag = False

        for item in permission_dict.values():
            regx = '^{}$'.format(item.get('url'))
            if re.match(regx, current_url):
                flag = True
                request.current_selected_permission = item.get('pid') or item.get('id')
                if item.get('pid'):
                    # 三级路径导航
                    url_record.extend([
                        {'title': item.get('p_title'), 'url': item.get('p_url')},
                        {'title': item.get('title'), 'url': item.get('url'), 'class': 'active'}
                    ])
                else:
                    url_record.extend([{'title': item.get('title'), 'url': item.get('url'), 'class': 'active'}])
                print(url_record)
                break
        request.url_record = url_record

        if not flag:
            return HttpResponse('无权访问')