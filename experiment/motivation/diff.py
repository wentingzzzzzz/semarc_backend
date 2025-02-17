
# 定义两个簇的文件列表
cluster1 = [
    "lib/intl/ngettext.c",
    "lib/intl/l10nflist.c",
    "lib/intl/dngettext.c",
    "lib/intl/textdomain.c",
    "lib/intl/dcgettext.c",
    "lib/intl/log.c",
    "lib/intl/gettext.c",
    "lib/intl/bindtextdom.c",
    "lib/intl/plural-exp.h",
    "lib/intl/plural.c",
    "lib/intl/dgettext.c",
    "lib/intl/explodename.c",
    "lib/intl/gmo.h",
    "lib/intl/loadmsgcat.c",
    "lib/intl/eval-plural.h",
    "lib/intl/finddomain.c",
    "lib/intl/gettextP.h",
    "lib/intl/dcigettext.c",
    "lib/intl/intl-compat.c",
    "lib/intl/hash-string.h",
    "lib/intl/loadinfo.h",
    "lib/intl/localealias.c",
    "lib/intl/dcngettext.c",
    "lib/intl/osdep.c",
    "lib/intl/plural-exp.c"
]

cluster2 = [
    "lib/intl/osdep.c",
    "lib/intl/localename.c",
    "lib/intl/log.c",
    "lib/intl/os2compat.c",
    "lib/intl/bindtextdom.c",
    "lib/intl/dcgettext.c",
    "lib/intl/dcigettext.c",
    "lib/intl/dcngettext.c",
    "lib/intl/dgettext.c",
    "lib/intl/dngettext.c",
    "lib/intl/eval-plural.h",
    "lib/intl/explodename.c",
    "lib/intl/finddomain.c",
    "lib/intl/gettext.c",
    "lib/intl/gettextP.h",
    "lib/intl/gmo.h",
    "lib/intl/hash-string.h",
    "lib/intl/intl-compat.c",
    "lib/intl/l10nflist.c",
    "lib/intl/loadinfo.h",
    "lib/intl/loadmsgcat.c",
    "lib/intl/localcharset.c",
    "lib/intl/localcharset.h",
    "lib/intl/localealias.c",
    "lib/intl/ngettext.c",
    "lib/intl/plural-exp.c",
    "lib/intl/plural-exp.h",
    "lib/intl/plural.c",
    "lib/intl/plural.y",
    "lib/intl/relocatable.c",
    "lib/intl/relocatable.h",
    "lib/intl/textdomain.c"
]

# 将文件列表转换为集合
set1 = set(cluster1)
set2 = set(cluster2)

# 找出差异
diff1 = set1 - set2
diff2 = set2 - set1

# 输出差异
print("Cluster 1 中独有的文件:", diff1)
print("Cluster 2 中独有的文件:", diff2)
