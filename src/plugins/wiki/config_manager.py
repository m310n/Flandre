import re
from typing import Type

# from mediawiki import MediaWiki
from .mediawiki import MediaWiki
from nonebot import on_command
from nonebot.adapters.cqhttp import Bot, GroupMessageEvent, Event, Message
from nonebot.adapters.cqhttp.permission import GROUP_OWNER, GROUP_ADMIN, GROUP, PRIVATE
from nonebot.matcher import Matcher
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from .config import Config


'''
设置管理器部分大量借(chao)鉴(xi)了 nonebot-hk-reporter 插件（以MIT许可证授权）的源码
Github地址：https://github.com/felinae98/nonebot-hk-reporter
协议：https://github.com/felinae98/nonebot-hk-reporter/blob/main/LICENSE
'''

def _gen_prompt_template(prompt: str):
    if hasattr(Message, 'template'):
        return Message.template(prompt)
    return prompt


def do_add_wiki(add_wiki: Type[Matcher]):
    @add_wiki.handle()
    async def init_promote(bot: Bot, event: Event, state: T_State):
        await init_promote_public(bot, event, state)

    async def parse_prefix(bot: Bot, event: Event, state: T_State) -> None:
        await parse_prefix_public(add_wiki, bot, event, state)

    @add_wiki.got('prefix', _gen_prompt_template('{_prompt}'), parse_prefix)
    @add_wiki.handle()
    async def init_api_url(bot: Bot, event: Event, state: T_State):
        await init_api_url_public(bot, event, state)

    async def parse_api_url(bot: Bot, event: Event, state: T_State):
        await parse_api_url_public(add_wiki, bot, event, state)

    @add_wiki.got('api_url', _gen_prompt_template('{_prompt}'), parse_api_url)
    @add_wiki.handle()
    async def init_url(bot: Bot, event: Event, state: T_State):
        await init_url_public(bot, event, state)

    async def parse_url(bot: Bot, event: Event, state: T_State):
        await parse_url_public(add_wiki, bot, event, state)

    @add_wiki.got('url', _gen_prompt_template('{_prompt}'), parse_url)
    @add_wiki.handle()
    async def add_wiki_process(bot: Bot, event: GroupMessageEvent, state: T_State):
        await add_wiki_all_process_public(event.group_id, add_wiki, bot, event, state)


def do_query_wikis(query_wikis: Type[Matcher]):
    @query_wikis.handle()
    async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
        await __public(event.group_id, query_wikis, bot, event, state)


def do_del_wiki(del_wiki: Type[Matcher]):
    @del_wiki.handle()
    async def send_list(bot: Bot, event: GroupMessageEvent, state: T_State):
        await send_list_public(event.group_id, del_wiki, bot, event, state)

    @del_wiki.receive()
    async def do_del(bot, event: GroupMessageEvent, state: T_State):
        await do_del_public(event.group_id, del_wiki, bot, event, state)


def do_set_default(set_default: Type[Matcher]):
    @set_default.handle()
    async def send_list(bot: Bot, event: GroupMessageEvent, state: T_State):
        await send_list_public(event.group_id, set_default, bot, event, state)

    @set_default.receive()
    async def do_set(bot, event: GroupMessageEvent, state: T_State):
        await do_set_public(event.group_id, set_default, bot, event, state)


'''
全局wiki设置
'''


def do_add_wiki_global(add_wiki_global: Type[Matcher]):
    @add_wiki_global.handle()
    async def init_promote(bot: Bot, event: Event, state: T_State):
        await init_promote_public(bot, event, state)

    async def parse_prefix(bot: Bot, event: Event, state: T_State) -> None:
        await parse_prefix_public(add_wiki_global, bot, event, state)

    @add_wiki_global.got('prefix', _gen_prompt_template('{_prompt}'), parse_prefix)
    @add_wiki_global.handle()
    async def init_api_url(bot: Bot, event: Event, state: T_State):
        await init_api_url_public(bot, event, state)

    async def parse_api_url(bot: Bot, event: Event, state: T_State):
        await parse_api_url_public(add_wiki_global, bot, event, state)

    @add_wiki_global.got('api_url', _gen_prompt_template('{_prompt}'), parse_api_url)
    @add_wiki_global.handle()
    async def init_url(bot: Bot, event: Event, state: T_State):
        await init_url_public(bot, event, state)

    async def parse_url(bot: Bot, event: Event, state: T_State):
        await parse_url_public(add_wiki_global, bot, event, state)

    @add_wiki_global.got('url', _gen_prompt_template('{_prompt}'), parse_url)
    @add_wiki_global.handle()
    async def add_wiki_global_process(bot: Bot, event: Event, state: T_State):
        await add_wiki_all_process_public(0, add_wiki_global, bot, event, state)


def do_query_wikis_global(query_wikis_global: Type[Matcher]):
    @query_wikis_global.handle()
    async def _(bot: Bot, event: Event, state: T_State):
        await __public(0, query_wikis_global, bot, event, state)


def do_del_wiki_global(del_wiki_global: Type[Matcher]):
    @del_wiki_global.handle()
    async def send_list(bot: Bot, event: Event, state: T_State):
        await send_list_public(0, del_wiki_global, bot, event, state)

    @del_wiki_global.receive()
    async def do_del(bot, event: Event, state: T_State):
        await do_del_public(0, del_wiki_global, bot, event, state)


def do_set_default_global(set_default_global: Type[Matcher]):
    @set_default_global.handle()
    async def send_list(bot: Bot, event: Event, state: T_State):
        await send_list_public(0, set_default_global, bot, event, state)

    @set_default_global.receive()
    async def do_set(bot, event: Event, state: T_State):
        await do_set_public(0, set_default_global, bot, event, state)


'''
公用函数
'''


async def init_promote_public(bot: Bot, event: Event, state: T_State):
    # state['_prompt'] = "请输入要添加的Wiki的代号（仅字母、数字、下划线），这将作为条目名前用于标识的前缀\n" + \
    #                    "如将“萌娘百科”设置为moe，从中搜索条目“芙兰朵露“的命令为：[[moe:芙兰朵露]]\n" + \
    #                    "另：常用的名字空间及其缩写将不会被允许作为代号，例如Special、Help、Template等；" + \
    #                    "也勿将wiki的项目名字空间作为代号，否则可能产生冲突\n" + \
    #                    "回复“取消”以中止"
    state['_prompt'] = "请回复前缀："


async def parse_prefix_public(parameter: Type[Matcher], bot: Bot, event: Event, state: T_State) -> None:
    prefix = str(event.get_message()).strip().lower()
    reserved = ["(main)", "talk", "user", "user talk", "project", "project talk", "file", "file talk", "mediawiki",
                "mediawiki talk", "template", "template talk", "help", "help talk", "category", "category talk",
                "special", "media", "t", "u"]
    if prefix == "取消":
        await parameter.finish("OK")
    elif prefix in reserved:
        await parameter.reject("前缀位于保留名字空间！请重新输入！")
    elif re.findall('\W', prefix):
        await parameter.reject("前缀含有非法字符，请重新输入！")
    else:
        state['prefix'] = prefix


async def init_api_url_public(bot: Bot, event: Event, state: T_State):
    # state['_prompt'] = "请输入wiki的api地址，通常形如这样：\n" + \
    #                    "https://www.example.org/w/api.php\n" + \
    #                    "https://www.example.org/api.php\n" \
    #                    "如果托管bot的服务器所在的国家/地区无法访问某些wiki的api，或者该wiki不提供api,你也可以回复empty来跳过输入"
    state['_prompt'] = "请输入wiki的api地址，回复empty跳过"


async def parse_api_url_public(parameter: Type[Matcher], bot: Bot, event: Event, state: T_State):
    api_url = str(event.get_message()).strip()
    if api_url.lower() == 'empty':
        state['api_url'] = ''
    elif api_url == '取消':
        await parameter.finish("OK")
    elif not re.match(r'^https?:/{2}\w.+$', api_url):
        await parameter.reject("非法url!请重新输入！")
    else:
        if not MediaWiki.test_api(api_url):
            await parameter.reject("无法连接到api，请重新输入！如果确认无误的话，可能是被防火墙拦截，可以输入“empty”跳过，或者“取消”来退出")
        state['api_url'] = api_url.strip().rstrip("/")


async def init_url_public(bot: Bot, event: Event, state: T_State):
    # state['_prompt'] = '请输入wiki的通用url，通常情况下，由该url与条目名拼接即可得到指向条目的链接，如：\n' + \
    #                    '中文维基百科：https://zh.wikipedia.org/wiki/\n' + \
    #                    '萌娘百科：https://zh.moegirl.org.cn/\n' + \
    #                    '另请注意：该项目不允许置空'
    state['_prompt'] = '请输入wiki的通用url（不允许留空）'


async def parse_url_public(parameter: Type[Matcher], bot: Bot, event: Event, state: T_State):
    url = str(event.get_message()).strip()
    if url == "取消":
        await parameter.finish("OK")
    elif not re.match(r'^https?:/{2}\w.+$', url):
        await parameter.reject("非法url！请重新输入！")
    else:
        state['url'] = url.strip().rstrip("/")


async def add_wiki_all_process_public(group_id: int, parameter: Type[Matcher], bot: Bot, event: Event, state: T_State):
    config: Config = Config(group_id)
    prefix: str = state["prefix"]
    api_url: str = state["api_url"]
    url: str = state["url"]
    if group_id == 0 and config.add_wiki_global(prefix, api_url, url):
        await parameter.finish(f"添加/编辑Wiki: {prefix} 成功！")
    elif config.add_wiki(prefix, api_url, url):
        await parameter.finish(f"添加/编辑Wiki: {prefix} 成功！")
    else:
        await parameter.finish("呜……出错了……如果持续出现，请联系bot管理员进行排查")


async def __public(group_id: int, parameter: Type[Matcher], bot: Bot, event: Event, state: T_State):
    config: Config = Config(group_id)
    all_data: tuple = config.list_data
    all_data_str: str = all_data[1] if group_id == 0 else all_data[0] + all_data[1]
    await parameter.finish(all_data_str)


async def send_list_public(group_id: int, parameter: Type[Matcher], bot: Bot, event: Event, state: T_State):
    config: Config = Config(group_id)
    tmp_str = "全局" if group_id == 0 else "本群"
    res = f"以下为{tmp_str}绑定的所有wiki列表，请回复前缀来选择wiki，回复“取消”退出：\n"
    res += config.list_data[1] if group_id == 0 else config.list_data[0]
    await parameter.send(message=Message(res))


async def do_del_public(group_id: int, parameter: Type[Matcher], bot, event: Event, state: T_State):
    prefix = str(event.get_message()).strip()
    if prefix == "取消":
        await parameter.finish("OK")
    else:
        config: Config = Config(group_id)
        if group_id == 0 and config.del_wiki_global(prefix):
            await parameter.finish("删除成功")
        elif config.del_wiki(prefix):
            await parameter.finish("删除成功")
        else:
            await parameter.finish("删除失败……请检查前缀是否有误")


# async def send_list_public(group_id: int, parameter: Type[Matcher], bot: Bot, event: Event, state: T_State):
#     config: Config = Config(group_id)
#     tmp_str = "全局" if group_id == 0 else "本群"
#     res = f"以下为{tmp_str}wiki列表，请回复前缀来选择要设为默认的wiki，回复“取消”退出：\n"
#     res += config.list_data[1]
#     await parameter.send(message=Message(res))


async def do_set_public(group_id: int, parameter: Type[Matcher], bot, event: Event, state: T_State):
    prefix = str(event.get_message()).strip()
    if prefix == "取消":
        await parameter.finish("OK")
    else:
        config: Config = Config(group_id)
        if group_id == 0 and config.set_default_global(prefix):
            await parameter.finish("设置成功")
        elif config.set_default(prefix):
            await parameter.finish("设置成功")
        else:
            await parameter.finish("设置失败……请检查前缀是否有误")


'''
Matchers
'''
add_wiki_matcher = on_command("添加wiki", aliases={"添加Wiki", "添加WIKI", "编辑wiki", "编辑Wiki", "编辑WIKI"},
                              permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)
do_add_wiki(add_wiki_matcher)
add_wiki_global_matcher = on_command("添加全局wiki", aliases={"添加全局WIKI", "添加全局Wiki", "编辑全局wiki", "编辑全局Wiki", "编辑全局WIKI"},
                                     permission=SUPERUSER)
do_add_wiki_global(add_wiki_global_matcher)

query_wikis_matcher = on_command("wiki列表", aliases={"查看wiki", "查看Wiki", "查询wiki", "查询Wiki", "Wiki列表"}, permission=GROUP)
do_query_wikis(query_wikis_matcher)
query_wikis_global_matcher = on_command("全局wiki列表",
                                        aliases={"查看全局wiki", "查看全局Wiki", "查询全局wiki", "查询全局Wiki", "全局Wiki列表"})
do_query_wikis_global(query_wikis_global_matcher)

del_wiki_matcher = on_command("删除wiki", aliases={"删除Wiki", "删除WIKI"}, permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)
do_del_wiki(del_wiki_matcher)
del_wiki_global_matcher = on_command("删除全局WIKI", aliases={"删除全局wiki", "删除全局Wiki"}, permission=SUPERUSER)
do_del_wiki_global(del_wiki_global_matcher)

set_default_matcher = on_command("设置默认wiki", aliases={"设置默认Wiki", "设置默认WIKI"},
                                 permission=SUPERUSER | GROUP_ADMIN | GROUP_OWNER)
do_set_default(set_default_matcher)
set_default_global_matcher = on_command("设置全局默认wiki",
                                        aliases={"设置全局默认Wiki", "设置全局默认WIKI", "全局默认wiki", "全局默认Wiki"},
                                        permission=SUPERUSER)
do_set_default_global(set_default_global_matcher)
