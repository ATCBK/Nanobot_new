FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

#为 WhatsApp 桥安装 Node.js 20
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates gnupg git && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" > /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get purge -y gnupg && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

#先安装Python依赖（缓存层）
COPY pyproject.toml README.md LICENSE ./
RUN mkdir -p nanobot bridge && touch nanobot/__init__.py && \
    uv pip install --system --no-cache . && \
    rm -rf nanobot bridge

#复制完整源并安装
COPY nanobot/ nanobot/
COPY bridge/ bridge/
RUN uv pip install --system --no-cache .

#搭建 WhatsApp 桥梁
WORKDIR /app/bridge
RUN npm install && npm run build
WORKDIR /app

#创建配置目录
RUN mkdir -p /root/.nanobot

#网关默认端口
EXPOSE 18790

ENTRYPOINT ["nanobot"]
CMD ["status"]
