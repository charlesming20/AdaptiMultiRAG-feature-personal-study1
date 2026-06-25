<template>
  <div class="h-screen flex bg-amber-50/30">
    <!-- 左侧边栏 -->
    <div class="w-80 bg-white border-r border-gray-100 flex flex-col shadow-sm">
      <!-- 头部 -->
      <div class="p-4 border-b border-gray-100">
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center space-x-2">
            <div
              class="w-7 h-7 rounded-lg bg-gray-900 flex items-center justify-center"
            >
              <svg
                class="w-4 h-4 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.959 8.959 0 01-4.906-1.471c-.905-.556-1.94-.808-3.094-.808-1.154 0-2.189.252-3.094.808A8.959 8.959 0 013 20c0-4.418 3.582-8 8-8s8 3.582 8 8z"
                />
              </svg>
            </div>
            <h1 class="text-lg font-medium text-gray-900">AdaptiMultiRAG</h1>
          </div>
          <button
            @click="logout"
            class="text-gray-500 hover:text-gray-900 p-2 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
              />
            </svg>
          </button>
        </div>
        <button
          @click="createNewConversation"
          class="w-full bg-gray-900 text-white py-2.5 px-4 rounded-lg hover:bg-gray-800 transition-colors flex items-center justify-center font-medium"
        >
          <svg
            class="w-4 h-4 mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 4v16m8-8H4"
            />
          </svg>
          新建对话
        </button>
      </div>

      <!-- 对话列表 -->
      <div class="flex-1 overflow-y-auto p-3">
        <div class="space-y-1">
          <div
            v-for="conversation in conversations"
            :key="conversation.id"
            @click="selectConversation(conversation.id)"
            class="p-3 rounded-lg cursor-pointer transition-all group"
            :class="{
              'bg-amber-50 border border-amber-200':
                currentConversation?.id === conversation.id,
              'hover:bg-gray-50 border border-transparent':
                currentConversation?.id !== conversation.id,
            }"
          >
            <div class="flex items-center justify-between">
              <div class="flex-1 min-w-0">
                <h3 class="text-sm font-normal text-gray-900 truncate">
                  {{ conversation.title }}
                </h3>
              </div>
              <button
                @click.stop="deleteConversation(conversation.id)"
                class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-gray-900 p-1 rounded transition-all"
              >
                <svg
                  class="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部导航 -->
      <div class="p-4 border-t border-gray-100">
        <router-link
          to="/document-library"
          class="block text-center py-2 px-3 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors font-normal"
        >
          文档库管理
        </router-link>
      </div>
    </div>

    <!-- 主聊天区域 -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- 聊天头部 -->
      <div
        class="bg-white/80 backdrop-blur-sm border-b border-gray-100 p-4 shadow-sm"
      >
        <h2 class="text-lg font-normal text-gray-900">
          {{ currentConversation?.title || "选择或创建一个对话" }}
        </h2>
      </div>

      <!-- 消息区域 -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4" ref="messagesContainer">
        <!-- 加载状态 -->
        <div
          v-if="loading && currentConversation"
          class="flex items-center justify-center h-full"
        >
          <div class="text-center">
            <div class="relative inline-block">
              <!-- 背景圆环 -->
              <div
                class="w-12 h-12 rounded-full border-4 border-gray-200"
              ></div>
              <!-- 旋转的蓝色圆环 -->
              <div
                class="absolute inset-0 w-12 h-12 rounded-full border-4 border-transparent border-t-blue-600 animate-spin"
              ></div>
            </div>
            <p class="text-gray-500 mt-4 text-sm">正在加载对话内容...</p>
            <!-- 添加一些点动画 -->
            <div class="flex justify-center mt-2 space-x-1">
              <div
                class="w-2 h-2 bg-blue-600 rounded-full animate-bounce"
              ></div>
              <div
                class="w-2 h-2 bg-blue-600 rounded-full animate-bounce"
                style="animation-delay: 0.1s"
              ></div>
              <div
                class="w-2 h-2 bg-blue-600 rounded-full animate-bounce"
                style="animation-delay: 0.2s"
              ></div>
            </div>
          </div>
        </div>

        <div
          v-else-if="!currentConversation"
          class="flex items-center justify-center h-full"
        >
          <div class="text-center text-gray-500">
            <svg
              class="w-16 h-16 mx-auto mb-4 text-gray-300"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.959 8.959 0 01-4.906-1.471c-.905-.556-1.94-.808-3.094-.808-1.154 0-2.189.252-3.094.808A8.959 8.959 0 013 20c0-4.418 3.582-8 8-8s8 3.582 8 8z"
              />
            </svg>
            <p class="text-lg font-medium mb-2">开始新的对话</p>
            <p class="text-sm">点击"新建对话"开始与AI助手聊天</p>
          </div>
        </div>

        <div
          v-else
          v-for="message in messages"
          :key="message.id"
          class="flex gap-4"
          :class="{
            'justify-end': message.role === 'user',
            '': message.role === 'assistant' || message.role === 'node_update',
          }"
        >
          <!-- 节点更新消息的可折叠渲染 -->
          <div v-if="message.role === 'node_update'" class="w-full max-w-3xl">
            <details class="node-update-details">
              <summary class="node-update-summary">
                <div class="node-update-caret">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </div>
                <div class="node-update-title">
                  <p>{{ getNodeDisplayName(message.node_name) }}</p>
                </div>
              </summary>
              <div class="node-update-content">
                <div class="node-update-content-text">
                  {{ message.content }}
                </div>
              </div>
            </details>
          </div>

          <!-- 普通消息渲染 -->
          <template v-else>
            <!-- 助手消息 -->
            <template v-if="message.role === 'assistant'">
              <!-- 头像 -->
              <div class="flex-shrink-0">
                <div
                  class="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center"
                >
                  <span class="text-sm font-semibold text-blue-600">AI</span>
                </div>
              </div>

              <!-- 消息内容 -->
              <div class="flex-1 max-w-3xl">
                <div
                  class="text-sm text-gray-700 prose prose-sm max-w-none"
                  v-html="renderMarkdown(message.content)"
                ></div>

                <!-- 操作按钮 -->
                <div class="flex items-center gap-2 mt-3">
                  <button
                    class="text-gray-400 hover:text-gray-600 p-1.5 rounded hover:bg-gray-100 transition-colors"
                    title="编辑"
                  >
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                      />
                    </svg>
                  </button>
                  <button
                    class="text-gray-400 hover:text-gray-600 p-1.5 rounded hover:bg-gray-100 transition-colors"
                    title="复制"
                  >
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                      />
                    </svg>
                  </button>
                  <button
                    class="text-gray-400 hover:text-gray-600 p-1.5 rounded hover:bg-gray-100 transition-colors"
                    title="朗读"
                  >
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
                      />
                    </svg>
                  </button>
                  <button
                    class="text-gray-400 hover:text-gray-600 p-1.5 rounded hover:bg-gray-100 transition-colors"
                    title="点赞"
                  >
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"
                      />
                    </svg>
                  </button>
                  <button
                    class="text-gray-400 hover:text-gray-600 p-1.5 rounded hover:bg-gray-100 transition-colors"
                    title="点踩"
                  >
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5"
                      />
                    </svg>
                  </button>
                  <button
                    class="text-gray-400 hover:text-gray-600 p-1.5 rounded hover:bg-gray-100 transition-colors"
                    title="重新生成"
                  >
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            </template>

            <!-- 用户消息 -->
            <template v-else>
              <div
                class="px-4 py-2 rounded-lg bg-gray-900 text-white max-w-xs lg:max-w-md"
              >
                <p class="text-sm whitespace-pre-wrap">{{ message.content }}</p>
              </div>
            </template>
          </template>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="bg-white border-t border-gray-100 p-4">
        <!-- 当前设置信息提示 -->
        <div class="mb-3 flex flex-wrap items-center gap-2 text-xs">
          <span class="text-gray-500 font-normal">当前设置:</span>
          <span
            class="px-2 py-1 bg-amber-50 text-gray-700 rounded border border-amber-200 font-light"
          >
            {{ getRagModeText(ragMode) }}
          </span>
          <span
            v-if="selectedLibrary"
            class="px-2 py-1 bg-blue-50 text-gray-700 rounded border border-blue-200 font-light"
          >
            📚 {{ getSelectedLibraryName(selectedLibrary) }}
          </span>
          <span
            v-else
            class="px-2 py-1 bg-gray-50 text-gray-500 rounded border border-gray-200 font-light"
          >
            未选择知识库
          </span>
        </div>

        <form @submit.prevent="sendMessage" class="flex space-x-4">
          <!-- 设置按钮 -->
          <button
            @click="openSettingsModal"
            type="button"
            class="bg-gray-50 text-gray-600 px-3 py-2 rounded-lg border border-gray-200 hover:bg-gray-100 hover:border-gray-300 focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 transition-colors"
            title="RAG设置"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
          </button>

          <input
            v-model="newMessage"
            type="text"
            placeholder="输入您的消息..."
            class="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-gray-900 focus:border-transparent bg-white"
            :disabled="streaming"
          />
          <button
            type="submit"
            :disabled="!newMessage.trim() || streaming"
            class="bg-gray-900 text-white px-6 py-2 rounded-lg hover:bg-gray-800 focus:ring-2 focus:ring-gray-900 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          </button>
        </form>
      </div>
    </div>

    <!-- 右侧Agent架构图面板 -->
    <div
      :style="{ width: agentPanelWidth + 'px' }"
      class="bg-gradient-to-br from-amber-50/50 to-orange-50/50 border-l border-gray-100 flex flex-col overflow-hidden flex-shrink-0 relative"
    >
      <!-- 左侧拖动条 -->
      <div
        @mousedown="startResize"
        class="absolute left-0 top-0 bottom-0 w-1.5 cursor-col-resize hover:bg-gray-300 transition-colors z-10 group"
        :class="{ 'bg-gray-400': isResizing }"
      >
        <!-- 可视化拖动指示器 -->
        <div
          class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-1 h-12 bg-gray-300 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
        ></div>
      </div>

      <!-- 面板头部 -->
      <div class="p-4 border-b border-gray-100">
        <h3 class="text-lg font-normal text-gray-900">Agent架构流程</h3>
        <p class="text-xs text-gray-500 mt-1 font-light">RAG智能体工作流程图</p>
      </div>

      <!-- Mermaid流程图 -->
      <div class="flex-1 overflow-y-auto p-4">
        <div class="mermaid-container" ref="mermaidContainer">
          <pre class="mermaid" id="agent-flowchart">
flowchart TD
    start(["开始"]) --> check_retrieval_needed["是否需要检索"]
    check_retrieval_needed -- 是 --> expand_subquestions["扩展子问题"]
    check_retrieval_needed -- 否 --> direct_answer["直接回答"]
    expand_subquestions --> classify_question_type{"判断检索类型"}
    classify_question_type -- 向量 --> vector_db_retrieval["向量数据库检索"]
    classify_question_type -- 图谱 --> graph_db_retrieval["图数据库检索"]
    vector_db_retrieval --> generate_answer["生成答案"]
    graph_db_retrieval --> generate_answer
    generate_answer --> end_node(["结束"])
    direct_answer --> end_node
          </pre>
        </div>

        <!-- 当前执行节点提示 -->
        <div
          v-if="currentExecutingNode"
          class="mt-4 p-3 bg-white/80 border border-gray-200 rounded-lg shadow-sm"
        >
          <div class="flex items-center space-x-2">
            <div class="w-2 h-2 bg-gray-900 rounded-full animate-pulse"></div>
            <span class="text-sm font-normal text-gray-900"
              >正在执行: {{ currentExecutingNode }}</span
            >
          </div>
        </div>
      </div>
    </div>

    <!-- 知识库选择提示弹窗 -->
    <BaseModal
      v-model="showLibrarySelectDialog"
      title="选择知识库"
      size="md"
      :close-on-click-outside="false"
    >
      <div class="space-y-4">
        <div
          class="flex items-start space-x-3 p-4 bg-amber-50 rounded-lg border border-amber-200"
        >
          <svg
            class="w-5 h-5 text-gray-700 flex-shrink-0 mt-0.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <div class="text-sm text-gray-800">
            <p class="font-normal mb-1">提示</p>
            <p class="font-light">
              选择一个知识库以获得更准确的回答，或选择"不使用知识库"直接与AI对话。
            </p>
          </div>
        </div>

        <div>
          <label class="block text-sm font-normal text-gray-700 mb-3"
            >请选择知识库</label
          >
          <div v-if="librariesLoading" class="text-center py-8">
            <div
              class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"
            ></div>
            <p class="text-sm text-gray-500 mt-3 font-light">
              正在加载知识库...
            </p>
          </div>
          <div
            v-else-if="knowledgeLibraries.length === 0"
            class="text-center py-8"
          >
            <EmptyState
              title="暂无知识库"
              description="您还没有创建任何知识库，请先到文档库管理页面创建。"
            >
              <template #action>
                <BaseButton variant="primary" @click="goToDocumentLibrary">
                  <template #icon>
                    <svg
                      class="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 4v16m8-8H4"
                      />
                    </svg>
                  </template>
                  创建知识库
                </BaseButton>
              </template>
            </EmptyState>
          </div>
          <div v-else class="space-y-2 max-h-64 overflow-y-auto">
            <label
              class="flex items-center p-4 border-2 rounded-xl cursor-pointer hover:bg-amber-50/50 transition-all duration-200"
              :class="{
                'border-gray-900 bg-amber-50': selectedLibraryForDialog === '',
                'border-gray-200': selectedLibraryForDialog !== '',
              }"
            >
              <input
                type="radio"
                value=""
                v-model="selectedLibraryForDialog"
                class="w-4 h-4 text-gray-900 bg-gray-100 border-gray-300 focus:ring-gray-900 focus:ring-2"
              />
              <div class="ml-3">
                <div class="text-sm font-normal text-gray-900">
                  不使用知识库
                </div>
                <div class="text-xs text-gray-500 font-light">
                  仅使用基础AI模型回答
                </div>
              </div>
            </label>
            <label
              v-for="library in knowledgeLibraries"
              :key="library.id"
              class="flex items-center p-4 border-2 rounded-xl cursor-pointer hover:bg-amber-50/50 transition-all duration-200"
              :class="{
                'border-gray-900 bg-amber-50':
                  selectedLibraryForDialog === library.id,
                'border-gray-200': selectedLibraryForDialog !== library.id,
              }"
            >
              <input
                type="radio"
                :value="library.id"
                v-model="selectedLibraryForDialog"
                class="w-4 h-4 text-gray-900 bg-gray-100 border-gray-300 focus:ring-gray-900 focus:ring-2"
              />
              <div class="ml-3 flex-1">
                <div class="text-sm font-normal text-gray-900">
                  {{ library.title }}
                </div>
                <div class="text-xs text-gray-500 font-light">
                  {{ library.description || "暂无描述" }}
                </div>
              </div>
              <span v-if="library.document_count" class="badge badge-primary">
                {{ library.document_count }} 个文档
              </span>
            </label>
          </div>
        </div>

        <div class="flex items-center space-x-2 text-xs text-gray-500">
          <input
            type="checkbox"
            id="dontShowAgain"
            v-model="dontShowLibrarySelectAgain"
            class="w-4 h-4 text-gray-900 bg-gray-100 border-gray-300 rounded focus:ring-gray-900 focus:ring-2"
          />
          <label for="dontShowAgain" class="cursor-pointer font-light"
            >不再显示此提示</label
          >
        </div>
      </div>

      <template #footer>
        <BaseButton variant="secondary" @click="skipLibrarySelection">
          跳过
        </BaseButton>
        <BaseButton variant="primary" @click="confirmLibrarySelection">
          确认选择
        </BaseButton>
      </template>
    </BaseModal>

    <!-- 设置弹窗 -->
    <div
      v-if="settingsModalOpen"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      @click="cancelSettingsModal"
    >
      <div
        class="bg-white rounded-xl shadow-[0_4px_16px_rgba(0,0,0,0.12)] border border-gray-100 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        @click.stop
      >
        <!-- 弹窗头部 -->
        <div
          class="flex items-center justify-between p-6 border-b border-gray-100"
        >
          <h3 class="text-lg font-normal text-gray-900">
            {{
              isSettingsForConversationSwitch ? "切换对话前请先设置" : "RAG设置"
            }}
          </h3>
          <button
            @click="cancelSettingsModal"
            class="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg
              class="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <!-- 弹窗内容 -->
        <div class="p-6 space-y-6">
          <!-- RAG模式选择 -->
          <div>
            <label class="block text-sm font-normal text-gray-700 mb-3"
              >RAG模式</label
            >
            <div class="space-y-2">
              <label
                v-for="option in ragOptions"
                :key="option.value"
                class="flex items-center p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-amber-50/50 transition-colors"
                :class="{
                  'border-gray-900 bg-amber-50': ragMode === option.value,
                }"
              >
                <input
                  type="radio"
                  :value="option.value"
                  v-model="ragMode"
                  class="w-4 h-4 text-gray-900 bg-gray-100 border-gray-300 focus:ring-gray-900 focus:ring-2"
                />
                <div class="ml-3">
                  <div class="text-sm font-normal text-gray-900">
                    {{ option.label }}
                  </div>
                  <div class="text-xs text-gray-500 font-light">
                    {{ getRagModeDescription(option.value) }}
                  </div>
                </div>
              </label>
            </div>
          </div>

          <!-- 知识库选择 -->
          <div>
            <label class="block text-sm font-normal text-gray-700 mb-3"
              >选择知识库</label
            >
            <div v-if="librariesLoading" class="text-center py-4">
              <div
                class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"
              ></div>
              <p class="text-sm text-gray-500 mt-2 font-light">
                正在加载知识库...
              </p>
            </div>
            <div
              v-else-if="knowledgeLibraries.length === 0"
              class="text-center py-4"
            >
              <p class="text-sm text-gray-500 font-light">暂无知识库</p>
            </div>
            <div v-else class="space-y-2 max-h-48 overflow-y-auto">
              <label
                class="flex items-center p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-amber-50/50 transition-colors"
                :class="{
                  'border-gray-900 bg-amber-50': selectedLibrary === '',
                }"
              >
                <input
                  type="radio"
                  value=""
                  v-model="selectedLibrary"
                  class="w-4 h-4 text-gray-900 bg-gray-100 border-gray-300 focus:ring-gray-900 focus:ring-2"
                />
                <div class="ml-3">
                  <div class="text-sm font-normal text-gray-900">
                    不使用知识库
                  </div>
                  <div class="text-xs text-gray-500 font-light">
                    仅使用基础AI模型回答
                  </div>
                </div>
              </label>
              <label
                v-for="library in knowledgeLibraries"
                :key="library.id"
                class="flex items-center p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-amber-50/50 transition-colors"
                :class="{
                  'border-gray-900 bg-amber-50': selectedLibrary === library.id,
                }"
              >
                <input
                  type="radio"
                  :value="library.id"
                  v-model="selectedLibrary"
                  class="w-4 h-4 text-gray-900 bg-gray-100 border-gray-300 focus:ring-gray-900 focus:ring-2"
                />
                <div class="ml-3">
                  <div class="text-sm font-normal text-gray-900">
                    {{ library.title }}
                  </div>
                  <div class="text-xs text-gray-500 font-light">
                    {{ library.description || "暂无描述" }}
                  </div>
                </div>
              </label>
            </div>
          </div>

          <!-- 高级设置 -->
          <div class="border-t border-gray-100 pt-6">
            <h4 class="text-sm font-normal text-gray-700 mb-4">高级设置</h4>

            <!-- 最大检索文档数量 -->
            <div class="mb-4">
              <label class="block text-sm font-normal text-gray-700 mb-2">
                最大检索文档数量: {{ maxRetrievalDocs }}
              </label>
              <input
                v-model.number="maxRetrievalDocs"
                type="range"
                min="1"
                max="10"
                class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
              />
              <div
                class="flex justify-between text-xs text-gray-500 mt-1 font-light"
              >
                <span>1</span>
                <span>10</span>
              </div>
            </div>

            <!-- 系统提示词 -->
            <div>
              <label class="block text-sm font-normal text-gray-700 mb-2"
                >系统提示词</label
              >
              <textarea
                v-model="systemPrompt"
                rows="4"
                class="w-full px-3 py-2 border border-gray-200 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent resize-none bg-white"
                placeholder="你是一个专业的RAG助手，能够基于检索到的信息提供准确的回答。"
              ></textarea>
            </div>
          </div>
        </div>

        <!-- 弹窗底部 -->
        <div
          class="flex items-center justify-end space-x-3 p-6 border-t border-gray-100"
        >
          <button
            v-if="isSettingsForConversationSwitch"
            @click="cancelSettingsModal"
            class="px-4 py-2 text-sm font-normal text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
          >
            取消
          </button>
          <button
            v-if="!isSettingsForConversationSwitch"
            @click="resetSettings"
            class="px-4 py-2 text-sm font-normal text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-900"
          >
            重置默认
          </button>
          <button
            @click="closeSettingsModal"
            class="px-4 py-2 text-sm font-normal text-white bg-gray-900 border border-transparent rounded-lg hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-900"
          >
            确定
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessageBox, ElMessage } from "element-plus";
import { useAuthStore } from "../stores/auth";
import { useChatStore } from "../stores/chat";
import { knowledgeAPI } from "../api/knowledge.js";
import MarkdownIt from "markdown-it";
import BaseModal from "@/components/BaseModal.vue";
import BaseButton from "@/components/BaseButton.vue";
import EmptyState from "@/components/EmptyState.vue";
import mermaid from "mermaid";

// 初始化markdown渲染器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  breaks: true,
});

const router = useRouter();
const authStore = useAuthStore();
const chatStore = useChatStore();

const newMessage = ref("");
const messagesContainer = ref(null);
const mermaidContainer = ref(null); // Mermaid容器引用
const currentExecutingNode = ref(""); // 当前执行的节点
let nodeHighlightTimer = null;
let lastActiveNodeGroup = null;
let highlightQueueTimer = null;
let pendingHighlightNode = null;
const NODE_HIGHLIGHT_DELAY_MS = 120;
const ragMode = ref("auto"); // 改为单选
const selectedLibrary = ref(""); // 改为单选
const knowledgeLibraries = ref([]); // 知识库列表
const librariesLoading = ref(false); // 知识库加载状态
const maxRetrievalDocs = ref(3); // 最大检索文档数量
const systemPrompt = ref(
  "你是一个专业的RAG助手，能够基于检索到的信息提供准确的回答。"
); // 系统提示词
const settingsModalOpen = ref(false); // 设置弹窗状态
const showLibrarySelectDialog = ref(false); // 知识库选择弹窗状态
const selectedLibraryForDialog = ref(""); // 弹窗中选择的知识库
const dontShowLibrarySelectAgain = ref(false); // 不再显示提示
const pendingConversationId = ref(null); // 待切换的对话ID（用于设置确认后切换）
const isSettingsForConversationSwitch = ref(false); // 标记设置对话框是否为切换对话触发

// Agent面板调整大小相关
const agentPanelWidth = ref(384); // 初始宽度 384px (w-96)
const isResizing = ref(false);
const startX = ref(0);
const startWidth = ref(0);

// 节点名称到流程图节点ID的映射
const nodeNameToId = {
  // 开始和结束节点
  start: "start", // 开始
  end: "end_node", // 结束

  // 主流程节点
  route_question: "check_retrieval_needed", // 是否需要检索
  check_retrieval_needed: "check_retrieval_needed", // 是否需要检索(别名)

  // 检索分支
  query_expansion: "expand_subquestions", // 由原始问题扩展子问题
  expand_subquestions: "expand_subquestions", // 由原始问题扩展子问题(别名)

  classify_question: "classify_question_type", // 判断原始问题类型
  classify_question_type: "classify_question_type", // 判断原始问题类型(别名)

  retrieve_from_vector: "vector_db_retrieval", // 适合使用向量数据库
  vector_db_retrieval: "vector_db_retrieval", // 向量数据库检索(别名)

  retrieve_from_graph: "graph_db_retrieval", // 适合使用图数据库
  graph_db_retrieval: "graph_db_retrieval", // 图数据库检索(别名)

  // 答案生成
  generate_answer: "generate_answer", // 生成答案结点
  direct_answer: "direct_answer", // 直接回答
};

// RAG选项配置
const ragOptions = [
  { value: "auto", label: "自动判断" },
  { value: "no_retrieval", label: "不开启检索" },
  { value: "vector_only", label: "向量检索" },
  { value: "graph_only", label: "图检索" },
];

// 计算属性
const conversations = computed(() => chatStore.conversations);
const currentConversation = computed(() => chatStore.currentConversation);
const messages = computed(() => chatStore.messages);
const streaming = computed(() => chatStore.streaming);
const loading = computed(() => chatStore.loading);

// 方法
const logout = () => {
  authStore.logout();
  router.push("/login");
};

const enqueueNodeHighlight = (nodeName) => {
  pendingHighlightNode = nodeName;
  if (highlightQueueTimer) {
    clearTimeout(highlightQueueTimer);
  }
  highlightQueueTimer = setTimeout(() => {
    const nodeToHighlight = pendingHighlightNode;
    pendingHighlightNode = null;
    highlightQueueTimer = null;
    if (nodeToHighlight) {
      highlightNode(nodeToHighlight);
    }
  }, NODE_HIGHLIGHT_DELAY_MS);
};

// 高亮流程图节点 - 带重试机制
const highlightNode = (nodeName, retryCount = 0) => {
  if (!mermaidContainer.value) {
    console.warn("⚠️ mermaidContainer不存在");
    return;
  }

  const nodeId = nodeNameToId[nodeName];
  if (!nodeId) {
    console.warn(`⚠️ 未找到节点映射: ${nodeName}`);
    return;
  }

  console.log(
    "🎯 准备高亮节点:",
    nodeName,
    "-> ID:",
    nodeId,
    retryCount > 0 ? `(重试${retryCount})` : ""
  );

  // 更新当前执行节点显示
  currentExecutingNode.value = getNodeDisplayName(nodeName);
  if (nodeHighlightTimer) {
    clearTimeout(nodeHighlightTimer);
    nodeHighlightTimer = null;
  }

  // 移除所有已有的高亮
  const svg = mermaidContainer.value.querySelector("svg");
  if (!svg) {
    console.warn("⚠️ SVG元素不存在");
    // 如果SVG还未渲染,重试
    if (retryCount < 3) {
      setTimeout(() => {
        highlightNode(nodeName, retryCount + 1);
      }, 300);
    }
    return;
  }

  // 清理残留的完成态；当前态会在找到新节点后切换为短暂完成态
  svg.querySelectorAll(".node-completed").forEach((el) => {
    el.classList.remove("node-completed");
  });

  // 改进的节点查找逻辑
  let currentNodeGroup = null;

  // 方案1: 通过ID精确匹配 (最常见的情况)
  currentNodeGroup = svg.querySelector(`#flowchart-${nodeId}-0`);

  if (!currentNodeGroup) {
    // 方案2: 查找所有可能的ID格式和选择器
    const possibleSelectors = [
      `#flowchart-${nodeId}`,
      `#${nodeId}`,
      `[id^="flowchart-${nodeId}"]`,
      `g.node[id*="${nodeId}"]`,
      `.node[id*="${nodeId}"]`,
    ];

    for (const selector of possibleSelectors) {
      try {
        currentNodeGroup = svg.querySelector(selector);
        if (currentNodeGroup) {
          console.log("✅ 找到节点，使用选择器:", selector);
          break;
        }
      } catch (e) {
        console.warn("选择器无效:", selector);
      }
    }
  }

  if (!currentNodeGroup) {
    // 方案3: 通过文本内容匹配(备用方案)
    const nodeDisplayName = getNodeDisplayName(nodeName);
    const allNodes = svg.querySelectorAll(
      'g.node, g.node.default, g[class*="node"]'
    );
    for (const node of allNodes) {
      const textContent = node.textContent.trim();
      if (textContent === nodeDisplayName) {
        currentNodeGroup = node;
        console.log("✅ 通过文本内容找到节点:", nodeDisplayName);
        break;
      }
    }
  }

  if (currentNodeGroup) {
    if (lastActiveNodeGroup && lastActiveNodeGroup !== currentNodeGroup) {
      lastActiveNodeGroup.classList.remove("node-active");
      lastActiveNodeGroup.classList.add("node-completed");
      const completedNode = lastActiveNodeGroup;
      nodeHighlightTimer = setTimeout(() => {
        completedNode.classList.remove("node-completed");
        nodeHighlightTimer = null;
      }, 800);
    }

    currentNodeGroup.classList.add("node-active");
    lastActiveNodeGroup = currentNodeGroup;
    console.log("✅ 已添加node-active类到节点:", nodeName);

    // 普通节点保持蓝色，直到下一步节点到来；结束节点蓝色后转绿色，再恢复默认色
    if (nodeName === "end") {
      nodeHighlightTimer = setTimeout(() => {
        if (currentNodeGroup) {
          currentNodeGroup.classList.remove("node-active");
          currentNodeGroup.classList.add("node-completed");
        }
        currentExecutingNode.value = "";
        lastActiveNodeGroup = null;
        nodeHighlightTimer = setTimeout(() => {
          currentNodeGroup.classList.remove("node-completed");
          nodeHighlightTimer = null;
        }, 800);
      }, 500);
    }
  } else {
    console.warn("⚠️ 未找到节点元素，nodeId:", nodeId, "nodeName:", nodeName);

    // 重试机制 - 如果是前几次重试,可能是Mermaid还未完全渲染
    if (retryCount < 3) {
      console.log(`🔄 将在300ms后重试...`);
      setTimeout(() => {
        highlightNode(nodeName, retryCount + 1);
      }, 300);
    } else {
      // 最后一次重试失败,打印调试信息
      console.log("📋 SVG中所有的节点元素:");
      const allNodes = Array.from(
        svg.querySelectorAll('g.node, g[class*="node"]')
      );
      allNodes.forEach((node, index) => {
        console.log(`节点${index}:`, {
          id: node.id,
          class: node.className.baseVal || node.className,
          text: node.textContent.trim().substring(0, 30),
        });
      });
    }
  }
};

// 清除所有节点高亮
const clearNodeHighlights = () => {
  if (nodeHighlightTimer) {
    clearTimeout(nodeHighlightTimer);
    nodeHighlightTimer = null;
  }
  if (highlightQueueTimer) {
    clearTimeout(highlightQueueTimer);
    highlightQueueTimer = null;
  }
  pendingHighlightNode = null;
  lastActiveNodeGroup = null;
  currentExecutingNode.value = "";
  if (!mermaidContainer.value) return;

  const svg = mermaidContainer.value.querySelector("svg");
  if (svg) {
    svg.querySelectorAll(".node-active, .node-completed").forEach((el) => {
      el.classList.remove("node-active", "node-completed");
    });
  }
};

const createNewConversation = async () => {
  chatStore.createLocalConversation();
};

const selectConversation = async (conversationId) => {
  // 如果点击的是当前对话，不做任何操作
  if (currentConversation.value?.id === conversationId) {
    return;
  }

  // 保存待切换的对话ID
  pendingConversationId.value = conversationId;

  // 标记这是为了切换对话而打开的设置
  isSettingsForConversationSwitch.value = true;

  // 打开设置对话框
  settingsModalOpen.value = true;
};

const deleteConversation = async (conversationId) => {
  try {
    await ElMessageBox.confirm("确定要删除这个对话吗？", "删除确认", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });

    try {
      await chatStore.deleteConversation(conversationId);
      // 删除成功，可以添加成功提示
      console.log("对话删除成功");
    } catch (error) {
      console.error("删除对话失败:", error);
      // 可以在这里添加错误提示
      ElMessageBox.alert("删除对话失败，请稍后重试", "错误", {
        confirmButtonText: "确定",
        type: "error",
      });
    }
  } catch {
    // 用户取消删除
  }
};

const sendMessage = async () => {
  if (!newMessage.value.trim() || streaming.value) return;

  const message = newMessage.value.trim();
  newMessage.value = "";

  try {
    console.log("📤 准备发送消息");
    console.log("  当前选中的知识库ID:", selectedLibrary.value);
    console.log("  RAG模式:", ragMode.value);

    const messageData = {
      content: message,
      ragMode: ragMode.value,
      maxRetrievalDocs: maxRetrievalDocs.value,
      systemPrompt: systemPrompt.value,
    };

    // 只有在选中知识库时才添加collection_id
    if (selectedLibrary.value) {
      const collectionId = getSelectedLibraryCollectionId(
        selectedLibrary.value
      );
      console.log("  知识库collection_id:", collectionId);
      if (collectionId) {
        messageData.collection_id = collectionId;
      }
    } else {
      console.log("  未选择知识库，不添加collection_id");
    }
    console.log("📤 发送消息数据:", messageData);

    await chatStore.sendMessage(messageData);
    scrollToBottom();
  } catch (error) {
    console.error("发送消息失败:", error);
    // 可以在这里添加错误提示
  }
};

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
    }
  });
};

// 渲染markdown内容
const renderMarkdown = (content) => {
  return md.render(content);
};

// 获取节点显示名称
const getNodeDisplayName = (nodeName) => {
  const nodeNameMap = {
    start: "开始",
    check_retrieval_needed: "检索需求判断",
    expand_subquestions: "子问题扩展",
    classify_question_type: "问题类型分类",
    vector_db_retrieval: "向量数据库检索",
    graph_db_retrieval: "图数据库检索",
    graph_db_retrieval_node: "图数据库检索",
    generate_answer: "生成答案",
    direct_answer: "直接回答",
    answer_generation: "答案生成",
    end: "结束",
  };
  return nodeNameMap[nodeName] || nodeName;
};

// 加载知识库列表
const loadKnowledgeLibraries = async () => {
  try {
    librariesLoading.value = true;
    const response = await knowledgeAPI.getLibraries();

    if (response.status === 200) {
      knowledgeLibraries.value = response.data || [];
    } else {
      console.error("获取知识库列表失败:", response.msg);
      knowledgeLibraries.value = [];
    }
  } catch (error) {
    console.error("加载知识库列表失败:", error);
    knowledgeLibraries.value = [];
  } finally {
    librariesLoading.value = false;
  }
};

// 获取RAG模式文本（单选）
const getRagModeText = (mode) => {
  const option = ragOptions.find((opt) => opt.value === mode);
  return option ? option.label : mode;
};

// 获取选中知识库名称
const getSelectedLibraryName = (libraryId) => {
  const library = knowledgeLibraries.value.find((lib) => lib.id === libraryId);
  return library ? library.title : "未知知识库";
};

// 获取选中知识库的collection_id
const getSelectedLibraryCollectionId = (libraryId) => {
  const library = knowledgeLibraries.value.find((lib) => lib.id === libraryId);
  return library ? library.collection_id : null;
};

// 监听点击外部关闭下拉框
onMounted(async () => {
  // 初始化Mermaid
  mermaid.initialize({
    startOnLoad: false, // 改为false,手动控制渲染时机
    theme: "default",
    flowchart: {
      useMaxWidth: true,
      htmlLabels: true,
      curve: "basis",
      padding: 20, // 增加内边距,避免边缘裁剪
    },
    // 禁用安全级别以允许更好的渲染
    securityLevel: "loose",
  });

  // 等待DOM渲染完成后手动渲染Mermaid图表
  await nextTick();
  if (mermaidContainer.value) {
    try {
      await mermaid.run({
        querySelector: ".mermaid",
      });
      console.log("✅ Mermaid图表渲染完成");
    } catch (error) {
      console.error("❌ Mermaid渲染失败:", error);
    }
  }

  // 恢复Agent面板宽度
  restorePanelWidth();

  // 加载聊天历史
  if (authStore.isAuthenticated) {
    try {
      await chatStore.loadChatHistory();
      // 加载知识库列表
      await loadKnowledgeLibraries();

      // 从本地存储加载RAG模式设置
      const savedRagMode = localStorage.getItem("ragMode");
      if (savedRagMode) {
        ragMode.value = savedRagMode;
      }

      // 从本地存储加载选中的知识库
      const savedLibrary = localStorage.getItem("selectedLibrary");
      if (savedLibrary) {
        selectedLibrary.value = savedLibrary;
      }

      // 检查是否需要显示知识库选择弹窗
      // 延迟一下，让页面先渲染完成
      setTimeout(() => {
        checkShowLibrarySelectDialog();
      }, 500);
    } catch (error) {
      console.error("加载聊天历史失败:", error);
    }
  } else {
    router.push("/login");
  }
});

// 监听消息变化，自动滚动到底部
watch(
  messages,
  (newMessages, oldMessages) => {
    console.log("🔄 Messages数组发生变化:");
    console.log("  新消息数量:", newMessages.length);
    console.log("  旧消息数量:", oldMessages ? oldMessages.length : 0);
    console.log("  最新消息:", newMessages[newMessages.length - 1]);

    // 检查最后一条消息
    const lastMessage = newMessages[newMessages.length - 1];

    // 如果是节点更新消息,高亮对应节点
    if (
      streaming.value &&
      lastMessage &&
      lastMessage.role === "node_update" &&
      !lastMessage.updated
    ) {
      console.log("🎯 检测到节点更新:", lastMessage.node_name);
      // 使用nextTick确保DOM已更新,再用延迟确保Mermaid已渲染
      // 增加延迟时间以确保Mermaid完全渲染完成
      nextTick(() => {
        setTimeout(() => {
          enqueueNodeHighlight(lastMessage.node_name);
        }, 50);
      });
    }

    // 如果是用户消息,清除之前的高亮
    if (lastMessage && lastMessage.role === "user") {
      clearNodeHighlights();
    }

    // 检查最后一条AI消息的内容变化
    const lastAiMessage = newMessages
      .filter((m) => m.role === "assistant")
      .pop();
    if (lastAiMessage) {
      console.log("  最后一条AI消息内容长度:", lastAiMessage.content.length);
      console.log(
        "  最后一条AI消息内容预览:",
        lastAiMessage.content.substring(0, 50) + "..."
      );
    }

    scrollToBottom();
  },
  { deep: true }
);

watch(streaming, (isStreaming) => {
  if (!isStreaming) {
    currentExecutingNode.value = "";
  }
});

// 添加一个专门监听消息内容变化的watcher
watch(
  () => messages.value.map((m) => m.content),
  (newContents, oldContents) => {
    console.log("📝 消息内容发生变化:");
    newContents.forEach((content, index) => {
      const oldContent = oldContents ? oldContents[index] : "";
      if (content !== oldContent) {
        console.log(`  消息${index}内容变化:`, {
          old: oldContent ? oldContent.substring(0, 30) + "..." : "空",
          new: content.substring(0, 30) + "...",
          length: content.length,
        });
      }
    });
  },
  { deep: true }
);

// 监听RAG模式变化并保存到本地存储
watch(ragMode, (newMode) => {
  console.log("🔄 RAG模式变化:", newMode);
  localStorage.setItem("ragMode", newMode);
});

// 监听知识库选择变化并保存到本地存储
watch(selectedLibrary, (newLibrary) => {
  console.log("🔄 知识库选择变化:", newLibrary);
  const libraryName = newLibrary
    ? getSelectedLibraryName(newLibrary)
    : "不使用知识库";
  console.log("  -> 知识库名称:", libraryName);
  localStorage.setItem("selectedLibrary", newLibrary);
});

// 检查认证状态
if (!authStore.isAuthenticated) {
  router.push("/login");
}

// 获取RAG模式描述
const getRagModeDescription = (mode) => {
  const descriptions = {
    auto: "系统自动判断是否需要检索知识库",
    no_retrieval: "直接使用AI模型回答，不检索知识库",
    vector_only: "仅使用向量检索获取相关文档",
    graph_only: "仅使用图检索获取相关文档",
  };
  return descriptions[mode] || "未知模式";
};

// 打开设置弹窗
const openSettingsModal = () => {
  isSettingsForConversationSwitch.value = false;
  settingsModalOpen.value = true;
};

// 关闭设置弹窗（确认保存）
const closeSettingsModal = async () => {
  settingsModalOpen.value = false;
  ElMessage.success("设置已保存");

  // 如果是为了切换对话而打开的设置，现在执行切换
  if (isSettingsForConversationSwitch.value && pendingConversationId.value) {
    await chatStore.selectConversation(pendingConversationId.value);

    // 重置标记
    isSettingsForConversationSwitch.value = false;
    pendingConversationId.value = null;
  }
};

// 取消设置弹窗（不保存）
const cancelSettingsModal = () => {
  settingsModalOpen.value = false;

  // 重置标记，不执行对话切换
  if (isSettingsForConversationSwitch.value) {
    isSettingsForConversationSwitch.value = false;
    pendingConversationId.value = null;
  }
};

// 重置设置
const resetSettings = () => {
  ragMode.value = "auto";
  selectedLibrary.value = "";
  maxRetrievalDocs.value = 3;
  systemPrompt.value =
    "你是一个专业的RAG助手，能够基于检索到的信息提供准确的回答。";
};

// 确认知识库选择
const confirmLibrarySelection = () => {
  selectedLibrary.value = selectedLibraryForDialog.value;

  // 保存到localStorage
  localStorage.setItem("selectedLibrary", selectedLibrary.value);

  // 如果选择了"不再显示"，保存到localStorage
  if (dontShowLibrarySelectAgain.value) {
    localStorage.setItem("dontShowLibrarySelect", "true");
  }

  showLibrarySelectDialog.value = false;
};

// 跳过知识库选择
const skipLibrarySelection = () => {
  // 如果选择了"不再显示"，保存到localStorage
  if (dontShowLibrarySelectAgain.value) {
    localStorage.setItem("dontShowLibrarySelect", "true");
  }

  showLibrarySelectDialog.value = false;
};

// 跳转到文档库管理页面
const goToDocumentLibrary = () => {
  showLibrarySelectDialog.value = false;
  router.push("/document-library");
};

// 检查是否需要显示知识库选择弹窗
const checkShowLibrarySelectDialog = () => {
  const dontShow = localStorage.getItem("dontShowLibrarySelect");
  const savedLibrary = localStorage.getItem("selectedLibrary");

  // 如果用户选择了"不再显示"或已经选择过知识库，则不显示弹窗
  if (dontShow === "true" || savedLibrary) {
    return;
  }

  // 显示知识库选择弹窗
  showLibrarySelectDialog.value = true;
  selectedLibraryForDialog.value = selectedLibrary.value;
};

// Agent面板调整大小相关函数
const startResize = (e) => {
  isResizing.value = true;
  startX.value = e.clientX;
  startWidth.value = agentPanelWidth.value;

  // 添加鼠标移动和释放事件监听
  document.addEventListener("mousemove", handleResize);
  document.addEventListener("mouseup", stopResize);

  // 防止文本选择
  e.preventDefault();
};

const handleResize = (e) => {
  if (!isResizing.value) return;

  // 计算新宽度 (向左拖动增加宽度,向右拖动减少宽度)
  const deltaX = startX.value - e.clientX;
  const newWidth = startWidth.value + deltaX;

  // 限制最小和最大宽度
  const minWidth = 300; // 最小300px
  const maxWidth = 800; // 最大800px

  if (newWidth >= minWidth && newWidth <= maxWidth) {
    agentPanelWidth.value = newWidth;
  }
};

const stopResize = () => {
  isResizing.value = false;

  // 移除事件监听
  document.removeEventListener("mousemove", handleResize);
  document.removeEventListener("mouseup", stopResize);

  // 保存宽度到localStorage
  localStorage.setItem("agentPanelWidth", agentPanelWidth.value.toString());
};

// 从localStorage恢复面板宽度
const restorePanelWidth = () => {
  const savedWidth = localStorage.getItem("agentPanelWidth");
  if (savedWidth) {
    const width = parseInt(savedWidth);
    if (width >= 300 && width <= 800) {
      agentPanelWidth.value = width;
    }
  }
};
</script>

<style scoped>
/* 滑块样式 */
.slider::-webkit-slider-thumb {
  appearance: none;
  height: 20px;
  width: 20px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.slider::-moz-range-thumb {
  height: 20px;
  width: 20px;
  border-radius: 50%;
  background: #3b82f6;
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

/* 节点更新样式 */
.node-update-details {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin: 8px 0;
  background: #f9fafb;
}

.node-update-summary {
  padding: 12px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  user-select: none;
  background: #f3f4f6;
  border-radius: 8px 8px 0 0;
}

.node-update-details[open] .node-update-summary {
  border-bottom: 1px solid #e5e7eb;
  border-radius: 8px 8px 0 0;
}

.node-update-caret {
  transition: transform 0.2s ease;
}

.node-update-details[open] .node-update-caret {
  transform: rotate(90deg);
}

.node-update-title {
  flex: 1;
}

.node-update-content {
  padding: 16px;
}

.node-update-content-text {
  color: #374151;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
}
</style>
