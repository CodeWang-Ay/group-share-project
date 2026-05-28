<template>
  <div class="flex-1 p-4 lg:p-6 overflow-y-auto">
    <div class="flex flex-col md:flex-row gap-6">
      <!-- 左侧分类导航 -->
      <aside class="w-full md:w-64 flex-shrink-0">
        <nav class="bg-white rounded-lg shadow-sm p-4">
          <ul class="space-y-1">
            <li>
              <a @click="switchSection(1)" :class="navClass(1)" class="block px-4 py-2 rounded-md font-medium cursor-pointer">
                <i class="fa fa-search mr-2"></i>学术论文检索
              </a>
            </li>
            <li>
              <a @click="switchSection(2)" :class="navClass(2)" class="block px-4 py-2 rounded-md font-medium cursor-pointer hover:bg-gray-50 transition-colors">
                <i class="fa fa-book mr-2"></i>文献管理与阅读
              </a>
            </li>
            <li>
              <a @click="switchSection(3)" :class="navClass(3)" class="block px-4 py-2 rounded-md font-medium cursor-pointer hover:bg-gray-50 transition-colors">
                <i class="fa fa-pencil mr-2"></i>论文写作与排版
              </a>
            </li>
            <li>
              <a @click="switchSection(4)" :class="navClass(4)" class="block px-4 py-2 rounded-md font-medium cursor-pointer hover:bg-gray-50 transition-colors">
                <i class="fa fa-flask mr-2"></i>科研数据与工具
              </a>
            </li>
            <li>
              <a @click="switchSection(5)" :class="navClass(5)" class="block px-4 py-2 rounded-md font-medium cursor-pointer hover:bg-gray-50 transition-colors">
                <i class="fa fa-comments mr-2"></i>学术交流与社区
              </a>
            </li>
            <li>
              <a @click="switchSection(6)" :class="navClass(6)" class="block px-4 py-2 rounded-md font-medium cursor-pointer hover:bg-gray-50 transition-colors">
                <i class="fa fa-paper-plane mr-2"></i>会议投稿
              </a>
            </li>
            <li>
              <a @click="switchSection(7)" :class="navClass(7)" class="block px-4 py-2 rounded-md font-medium cursor-pointer hover:bg-gray-50 transition-colors">
                <i class="fa fa-cubes mr-2"></i>LLM模型访问
              </a>
            </li>
            <li>
              <a @click="switchSection(8)" :class="navClass(8)" class="block px-4 py-2 rounded-md font-medium cursor-pointer hover:bg-gray-50 transition-colors">
                <i class="fa fa-briefcase mr-2"></i>找工作
              </a>
            </li>
          </ul>
        </nav>
      </aside>

      <!-- 右侧内容区域 -->
      <main class="flex-1">
        <!-- 1. 学术论文检索 -->
        <section v-show="currentSection === 1" class="mb-10">
          <div class="bg-white rounded-lg shadow-sm p-6">
            <h2 class="text-xl font-bold mb-4 flex items-center text-primary">
              <i class="fa fa-search mr-2"></i>一、学术论文检索
            </h2>

            <!-- 综合数据库 -->
            <div class="mb-6">
              <h3 class="text-lg font-semibold mb-3 text-gray-800">综合数据库</h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ToolCard title="Google Scholar" tag="综合" tagClass="bg-blue-50 text-blue-600"
                          desc="最通用的学术论文搜索引擎，涵盖多学科文献" url="https://scholar.google.com" />
                <ToolCard title="IEEE Xplore" tag="工程技术" tagClass="bg-blue-50 text-blue-600"
                          desc="电子工程、计算机科学领域核心文献数据库" url="https://ieeexplore.ieee.org" />
                <ToolCard title="Web of Science" tag="引文索引" tagClass="bg-blue-50 text-blue-600"
                          desc="权威的学术文献引文数据库，支持影响力分析" url="https://www.webofscience.com" />
                <ToolCard title="SCI-HUB" tag="开放获取" tagClass="bg-blue-50 text-blue-600"
                          desc="提供大量学术论文的免费访问与下载" url="https://sci-hub.se" />
              </div>
            </div>

            <!-- 开源论文 -->
            <div class="mb-6">
              <h3 class="text-lg font-semibold mb-3 text-gray-800">开源论文</h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ToolCard title="arXiv" desc="各类预印本（CS/Math/Physics）" url="https://arxiv.org" color="primary" />
                <ToolCard title="HAL" desc="法国科研公开存档系统" url="https://hal.archives-ouvertes.fr" color="primary" />
              </div>
            </div>

            <!-- 中文论文 -->
            <div class="mb-6">
              <h3 class="text-lg font-semibold mb-3 text-gray-800">中文论文</h3>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <ToolCard title="知网 CNKI" desc="中国最全中文论文库" url="https://www.cnki.net" color="primary" />
                <ToolCard title="万方数据" desc="中文学位论文与期刊数据库" url="https://www.wanfangdata.com.cn" color="primary" />
                <ToolCard title="维普网" desc="中文期刊论文数据库" url="https://www.cqvip.com" color="primary" />
              </div>
            </div>

            <!-- 学术论文 -->
            <div>
              <h3 class="text-lg font-semibold mb-3 text-gray-800">学术论文</h3>
              <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                <ToolCard title="SpringerLink" desc="Springer 出版社论文资源" url="https://link.springer.com" color="primary" />
                <ToolCard title="ScienceDirect" desc="Elsevier 出版社论文资源" url="https://www.sciencedirect.com" color="primary" />
                <ToolCard title="Wiley Online Library" desc="Wiley 出版社资源" url="https://onlinelibrary.wiley.com" color="primary" />
              </div>
            </div>
          </div>
        </section>

        <!-- 2. 文献管理与阅读工具 -->
        <section v-show="currentSection === 2" class="mb-10">
          <div class="bg-white rounded-lg shadow-sm p-6">
            <h2 class="text-xl font-bold mb-4 flex items-center text-secondary">
              <i class="fa fa-book mr-2"></i>二、文献管理与阅读工具
            </h2>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <!-- 文献管理 -->
              <div>
                <h3 class="text-lg font-semibold mb-3 text-gray-800 flex items-center">
                  <i class="fa fa-folder-open mr-2 text-secondary"></i>文献管理
                </h3>
                <div class="space-y-4">
                  <ToolCard title="Zotero" desc="免费开源，支持插件与标注" url="https://www.zotero.org" color="secondary" />
                  <ToolCard title="EndNote" desc="专业级引用管理工具" url="https://endnote.com" color="secondary" />
                  <ToolCard title="Mendeley" desc="文献云存储与协作" url="https://www.mendeley.com" color="secondary" />
                </div>
              </div>

              <!-- 阅读笔记与工具 -->
              <div>
                <h3 class="text-lg font-semibold mb-3 text-gray-800 flex items-center">
                  <i class="fa fa-sticky-note mr-2 text-secondary"></i>阅读笔记与工具
                </h3>
                <div class="space-y-4">
                  <ToolCard title="语雀" desc="结构化知识库，支持文档协作与版本管理" url="https://www.yuque.com" color="secondary" />
                  <ToolCard title="飞书" desc="集成文档、表格与协作功能的办公平台" url="https://www.feishu.cn" color="secondary" />
                  <ToolCard title="Notion" desc="笔记+文献整理一体化" url="https://www.notion.so" color="secondary" />
                  <ToolCard title="Obsidian" desc="Markdown 笔记与知识图谱" url="https://obsidian.md" color="secondary" />
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 3. 论文写作与排版工具 -->
        <section v-show="currentSection === 3" class="mb-10">
          <div class="bg-white rounded-lg shadow-sm p-6">
            <h2 class="text-xl font-bold mb-4 flex items-center text-accent">
              <i class="fa fa-pencil mr-2"></i>三、论文写作与排版工具
            </h2>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <!-- 写作排版 -->
              <div>
                <h3 class="text-lg font-semibold mb-3 text-gray-800 flex items-center">
                  <i class="fa fa-file-text mr-2 text-accent"></i>写作排版
                </h3>
                <div class="space-y-4">
                  <ToolCard title="Overleaf" desc="在线 LaTeX 写作平台" url="https://www.overleaf.com" color="accent" />
                  <ToolCard title="LaTeX Templates" desc="各类论文模板" url="https://www.latextemplates.com" color="accent" />
                </div>
              </div>

              <!-- 写作辅助 -->
              <div>
                <h3 class="text-lg font-semibold mb-3 text-gray-800 flex items-center">
                  <i class="fa fa-check-circle mr-2 text-accent"></i>写作辅助
                </h3>
                <div class="space-y-4">
                  <ToolCard title="Grammarly" desc="英语语法与写作纠错" url="https://www.grammarly.com" color="accent" />
                  <ToolCard title="QuillBot" desc="改写、润色与摘要生成" url="https://quillbot.com" color="accent" />
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 4. 科研数据与工具网站 -->
        <section v-show="currentSection === 4" class="mb-10">
          <div class="bg-white rounded-lg shadow-sm p-6">
            <h2 class="text-xl font-bold mb-4 flex items-center text-green-600">
              <i class="fa fa-flask mr-2"></i>四、科研数据与工具网站
            </h2>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <!-- 开源数据 -->
              <div>
                <h3 class="text-lg font-semibold mb-3 text-gray-800 flex items-center">
                  <i class="fa fa-database mr-2 text-green-600"></i>开源数据
                </h3>
                <div class="space-y-4">
                  <ToolCard title="Kaggle" desc="机器学习竞赛与数据集" url="https://www.kaggle.com" color="green" />
                  <ToolCard title="飞桨 AI Studio 星河社区" desc="包含海量AI数据集与模型的开源社区" url="https://aistudio.baidu.com/datasetoverview" color="green" />
                  <ToolCard title="天池数据集（阿里云）" desc="涵盖多领域的高质量开放数据集平台" url="https://tianchi.aliyun.com/dataset" color="green" />
                  <ToolCard title="书生·万卷 1.0" desc="大规模多模态开源数据集库" url="https://opendatalab.com/" color="green" />
                  <ToolCard title="和鲸数据集库" desc="集成数据获取、分析与分享的科研平台" url="https://www.heywhale.com/home/dataset" color="green" />
                  <ToolCard title="UCI Machine Learning Repository" desc="经典机器学习数据集" url="https://archive.ics.uci.edu/ml" color="green" />
                  <ToolCard title="Hugging Face Datasets" desc="NLP 与多模态数据集" url="https://huggingface.co/datasets" color="green" />
                </div>
              </div>

              <!-- 绘图与统计工具 -->
              <div>
                <h3 class="text-lg font-semibold mb-3 text-gray-800 flex items-center">
                  <i class="fa fa-bar-chart mr-2 text-green-600"></i>绘图与统计工具
                </h3>
                <div class="space-y-4">
                  <ToolCard title="Microsoft Visio" desc="专业流程图、架构图绘制工具，支持复杂图形排版" url="https://products.office.com/zh-cn/visio/flowchart-software" color="green" />
                  <ToolCard title="draw.io" desc="通用流程图绘制" url="https://app.diagrams.net" color="green" />
                  <ToolCard title="Plotly / ChartGPT" desc="可视化图表工具" url="https://plotly.com" color="green" />
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 5. 学术交流与社区平台 -->
        <section v-show="currentSection === 5" class="mb-10">
          <div class="bg-white rounded-lg shadow-sm p-6">
            <h2 class="text-xl font-bold mb-4 flex items-center text-orange-500">
              <i class="fa fa-comments mr-2"></i>五、学术交流与社区平台
            </h2>

            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <ToolCard title="GitHub" desc="代码、模型与论文实现共享" url="https://github.com" color="orange" />
              <ToolCard title="Reddit r/academia" desc="全球学者讨论区" url="https://www.reddit.com/r/academia" color="orange" />
              <ToolCard title="小红书" desc="科研经验、学习方法分享社区" url="https://www.xiaohongshu.com" color="orange" />
              <ToolCard title="知乎" desc="中文学术圈讨论" url="https://www.zhihu.com" color="orange" />
              <ToolCard title="CSDN" desc="IT技术、编程与科研工具教程平台" url="https://www.csdn.net" color="orange" />
              <ToolCard title="博客园" desc="程序员与科研人员技术博客社区" url="https://www.cnblogs.com" color="orange" />
              <ToolCard title="科学空间" desc="聚焦科研方法与学术工具的深度分享平台" url="https://kexue.fm" color="orange" />
              <ToolCard title="Stack Exchange - Academia" desc="学术问答平台" url="https://academia.stackexchange.com" color="orange" />
            </div>
          </div>
        </section>

        <!-- 6. 会议投稿 -->
        <section v-show="currentSection === 6" class="mb-10">
          <div class="bg-white rounded-lg shadow-sm p-6">
            <h2 class="text-xl font-bold mb-4 flex items-center text-red-500">
              <i class="fa fa-paper-plane mr-2"></i>六、会议投稿
            </h2>

            <!-- 顶会投稿 -->
            <div class="mb-6">
              <h3 class="text-lg font-semibold mb-3 text-gray-800">顶会投稿</h3>
              <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                  <thead>
                    <tr>
                      <th class="px-4 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase">会议名称</th>
                      <th class="px-4 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase">简称</th>
                      <th class="px-4 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase">官网</th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    <tr class="hover:bg-gray-50">
                      <td class="px-4 py-3 whitespace-nowrap font-medium text-gray-900">Annual Meeting of the Association for Computational Linguistics</td>
                      <td class="px-4 py-3 whitespace-nowrap text-gray-600">ACL</td>
                      <td class="px-4 py-3 whitespace-nowrap"><a href="https://www.aclweb.org" target="_blank" class="text-red-500 hover:underline text-sm">https://www.aclweb.org <i class="fa fa-external-link ml-1"></i></a></td>
                    </tr>
                    <tr class="hover:bg-gray-50">
                      <td class="px-4 py-3 whitespace-nowrap font-medium text-gray-900">Conference on Empirical Methods in Natural Language Processing</td>
                      <td class="px-4 py-3 whitespace-nowrap text-gray-600">EMNLP</td>
                      <td class="px-4 py-3 whitespace-nowrap"><a href="https://2024.emnlp.org" target="_blank" class="text-red-500 hover:underline text-sm">https://2024.emnlp.org <i class="fa fa-external-link ml-1"></i></a></td>
                    </tr>
                    <tr class="hover:bg-gray-50">
                      <td class="px-4 py-3 whitespace-nowrap font-medium text-gray-900">North American Chapter of the Association for Computational Linguistics</td>
                      <td class="px-4 py-3 whitespace-nowrap text-gray-600">NAACL</td>
                      <td class="px-4 py-3 whitespace-nowrap"><a href="https://naacl.org" target="_blank" class="text-red-500 hover:underline text-sm">https://naacl.org <i class="fa fa-external-link ml-1"></i></a></td>
                    </tr>
                    <tr class="hover:bg-gray-50">
                      <td class="px-4 py-3 whitespace-nowrap font-medium text-gray-900">International Conference on Computational Linguistics</td>
                      <td class="px-4 py-3 whitespace-nowrap text-gray-600">COLING</td>
                      <td class="px-4 py-3 whitespace-nowrap"><a href="https://coling.org" target="_blank" class="text-red-500 hover:underline text-sm">https://coling.org <i class="fa fa-external-link ml-1"></i></a></td>
                    </tr>
                    <tr class="hover:bg-gray-50">
                      <td class="px-4 py-3 whitespace-nowrap font-medium text-gray-900">Natural Language Processing and Chinese Computing</td>
                      <td class="px-4 py-3 whitespace-nowrap text-gray-600">NLPCC</td>
                      <td class="px-4 py-3 whitespace-nowrap"><a href="http://tcci.ccf.org.cn" target="_blank" class="text-red-500 hover:underline text-sm">http://tcci.ccf.org.cn <i class="fa fa-external-link ml-1"></i></a></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- 会议快速投稿 -->
            <div>
              <h3 class="text-lg font-semibold mb-3 text-gray-800">会议快速投稿</h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <ToolCard title="CCF Deadline" desc="CCF会议截止日期查询" url="https://ccfddl.com" color="red" />
                <ToolCard title="CCFDDL 投稿" desc="CCF会议投稿辅助平台" url="https://ccfddl.top" color="red" />
              </div>
            </div>
          </div>
        </section>

        <!-- 7. LLM模型访问 -->
        <section v-show="currentSection === 7" class="mb-10">
          <div class="bg-white rounded-lg shadow-sm p-6">
            <h2 class="text-xl font-bold mb-4 flex items-center text-purple-600">
              <i class="fa fa-robot mr-2"></i>七、LLM模型访问
            </h2>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <LLMCard title="ChatGPT" desc="OpenAI 推出的现象级对话大模型，支持代码/创意/推理" url="https://chat.openai.com" icon="G" gradient="from-emerald-400 to-teal-500" />
              <LLMCard title="Claude" desc="Anthropic 出品的长文本、安全对齐大模型" url="https://claude.ai" icon="C" gradient="from-orange-400 to-amber-500" />
              <LLMCard title="Gemini" desc="Google 出品的长文本、gemini" url="https://gemini.google.com" icon="G" gradient="from-blue-400 to-blue-500" />
              <LLMCard title="DeepSeek" desc="深度求索推出的中英文多模态大模型，专注代码与数学推理" url="https://www.deepseek.com" icon="D" gradient="from-blue-500 to-indigo-600" />
              <LLMCard title="Kimi" desc="月之暗面出品、中文长文本友好的国产大模型" url="https://kimi.moonshot.cn" icon="K" gradient="from-purple-500 to-violet-600" />
              <LLMCard title="GLM" desc="智谱 AI 最新一代中英双语对话大模型" url="https://chatglm.cn" icon="G" gradient="from-cyan-400 to-blue-500" />
              <LLMCard title="豆包" desc="字节跳动旗下、集成搜索与插件的 AI 助手" url="https://www.doubao.com" icon="豆" gradient="from-red-400 to-rose-500" />
              <LLMCard title="Qwen（通义千问）" desc="阿里通义千问系列，开源+商用双版本" url="https://tongyi.aliyun.com/qianwen" icon="Q" gradient="from-orange-500 to-red-500" />
              <LLMCard title="文心一言" desc="百度打造的国产知识增强大模型" url="https://yiyan.baidu.com" icon="文" gradient="from-blue-600 to-blue-800" />
            </div>
          </div>
        </section>

        <!-- 8. 找工作 -->
        <section v-show="currentSection === 8" class="mb-10">
          <div class="bg-white rounded-lg shadow-sm p-6">
            <h2 class="text-xl font-bold mb-4 flex items-center text-teal-600">
              <i class="fa fa-briefcase mr-2"></i>八、找工作
            </h2>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <ToolCard title="LeetCode" desc="全球程序员刷题、面试题库与竞赛平台" url="https://leetcode.cn" color="teal" />
              <ToolCard title="牛客" desc="国内校招/实习/面经/题库一站式求职社区" url="https://www.nowcoder.com" color="teal" />
              <ToolCard title="赛码网" desc="专注算法竞赛与名企笔试真题的刷题平台" url="https://www.saima.wang" color="teal" />
              <ToolCard title="Boss 直聘" desc="直接与 HR/老板在线沟通的招聘平台" url="https://www.zhipin.com" color="teal" />
              <ToolCard title="代码随想录" desc="开源免费、系统刷题路线与图文题解仓库" url="https://programmercarl.com" color="teal" />
              <ToolCard title="知识星球" desc="付费社群聚集地，可跟随技术大 V 获取内推与干货" url="https://www.zsxq.com" color="teal" />
            </div>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ToolCard from '../components/ToolCard.vue'
import LLMCard from '../components/LLMCard.vue'

const currentSection = ref(1)

function navClass(section) {
  return currentSection.value === section
    ? 'bg-primary/10 text-primary border-l-4 border-primary'
    : 'hover:bg-gray-50 transition-colors'
}

function switchSection(section) {
  currentSection.value = section
}
</script>