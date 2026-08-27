# 快消品WMS系统 AI 维护交接文档

最后更新：2026-08-27  
当前应用版本：`0.5.9`

## 1. 项目定位

这是商贸公司的 ERPNext 二次开发应用。目标是解决“货物从中心仓发出，但尚未交付给客户”期间，中心仓实物库存与系统库存不一致的问题。

系统通过 ERPNext 原生单据实现库存控制：

```text
销售订单（在途交付）
        |
        | 提交后自动创建草稿，仓库核准后提交
        v
物料移动 / Stock Entry（核准提交时：中心仓 -> 客户在途仓）
        |
        | 客户实际签收后创建
        v
销售出库单 / Delivery Note（从客户在途仓出库）
```

不要修改 ERPNext 或 Frappe 核心代码。所有定制必须保留在 `fmcg_wms` 应用中。

## 2. 代码与运行环境

| 项目 | 当前值 |
| --- | --- |
| 中文名称 | 快消品WMS系统 |
| Python 应用名 | `fmcg_wms` |
| GitHub 仓库 | `https://github.com/mrechocc/fmcg_wms` |
| 本机代码目录 | `D:\AI\github\fmcg_wms` |
| 服务器 Bench | `/home/frappe/erpnext-bench` |
| 服务器操作用户 | `frappe` |
| 站点 | `wms.920530.xyz` |
| Frappe | `16.31.0` |
| ERPNext | `16.32.3` |
| erpnext_china | `1.0.23` |
| 当前应用版本 | `0.5.9` |

GitHub 是代码唯一来源。Windows 本机使用 GitHub Desktop 提交并 Push；服务器只执行 `git pull upstream main`，不要直接在服务器修改应用文件。

## 3. 已确认的仓库设置

当前公司使用的仓库如下：

| 用途 | 仓库名称 | 必要条件 |
| --- | --- | --- |
| 中心仓 | `中心仓库 - 道远行至` | 非组仓库；建议设为 Company Default Warehouse |
| 客户在途仓 | `客户在途仓 - 道远行至` | 非组仓库；Warehouse Type 必须为 `Transit`；公司必须相同 |

当前逻辑要求每个公司仅有一个启用的、非组的 `Transit` 仓库。若存在两个或更多中转仓，自动调拨会明确报错，不会任意选仓。

## 4. 业务规则

### 4.0 客户默认交付模式与外部 ERP 导入

客户资料新增“默认交付模式”：普通客户使用“当场交付”，大客户/缺货客户使用“在途交付”。销售订单会从客户自动带入该值，但用户仍可在订单上手工调整。

新增 `External ERP Import` 单据，仅限 `System Manager` 使用。先上传 Excel，再点击“预览并校验”；校验通过后才可“执行导入”。默认只创建草稿，不影响库存；勾选“校验后提交单据”才会提交 Sales Order 或 Delivery Note。

导入前必须维护以下外部编码：

| ERPNext 资料 | 自定义字段 | 外部 ERP 来源字段 |
| --- | --- | --- |
| Customer | `fmcg_external_customer_code` | 客户编码 |
| Item | `fmcg_external_item_code` | 存货编码 |
| Warehouse | `fmcg_external_warehouse_code` | 仓库编码 |

销售订单按 `单据编号` 写入 `fmcg_external_order_no`；销货单按 `单据编号` 写入 `fmcg_external_delivery_no`，重复上传时会跳过已导入单据。销货明细通过“销售订单号 + 存货编码 + 赠品”匹配 Sales Order Item，因此正价品与赠品不会合并。若外部系统存在同一订单、同一物料、同一赠品标记的重复明细，必须增加稳定的明细行号后再导入。

外部销货单中的负数量视为退货/冲销，导入器会列为异常而不创建正常销售出库单。对于在途订单，现有 Delivery Note 校验仍会强制使用在途仓，并阻止出库数量超过已核准且未送货的调拨数量。

### 4.1 当场交付

1. 销售订单的“交付模式”选择“当场交付”。
2. 提交销售订单不会创建物料移动。
3. 在“发货”菜单选择“确认当场交付”。
4. 系统从中心仓创建并提交销售出库单。

### 4.2 在途交付

1. 销售订单的“交付模式”选择“在途交付”。
2. 提交销售订单时，系统自动创建一张原生“物料移动”草稿，并打开该单据。草稿不影响任何库存。
3. 仓库人员将明细行数量改为本次实际可发数量，删除无货行，点击“核准并提交”。只有此时才从中心仓调入在途仓。
4. 同一销售订单可多次创建调拨；系统按订单行累计已核准数量，防止超过订单数量。每次只允许存在一张待核准草稿。
5. 调拨来源为订单商品行仓库；没有行仓库时使用订单出货仓；仍没有时使用公司默认中心仓。调拨目标为唯一的 `Transit` 仓库。
6. 销售订单的“发货”菜单可查看全部物料移动、打开待核准调拨、创建本次调拨，以及查看“待送货明细”。明细按订单行显示订单数量、已核准调拨、已送货、本次可送和尚未调拨数量。
7. “创建本次送货单”只在存在已核准调拨后可用。它创建一张 Delivery Note 草稿，并且只带入每个订单行“已核准且未送货”的数量；未调拨的商品不会进入送货单。用户可以在草稿中继续减少本次数量，提交时前端和后端都强制从客户在途仓出库，且后端会防止超量签收。WMS 会移除原生“创建 -> Delivery Note”入口，不能用原生整单映射替代该按钮。
8. 销售订单“创建”菜单会隐藏拣货单、生产工单、生产计划、物料需求、原材料物料需求、采购订单、项目、收付款申请和预收款。销售发票保留给财务使用；送货必须从“发货”菜单创建。

因此，物料移动完成后中心仓立即减少；客户真正签收时，销售出库单从在途仓减少。不要手工把在途订单的销售出库单改回中心仓。

## 5. 使用的原生单据

| 业务目的 | ERPNext DocType | 说明 |
| --- | --- | --- |
| 业务起点 | `Sales Order` | 选择交付模式、记录客户和订单数量 |
| 中心仓转在途仓 | `Stock Entry` | Purpose 为 `Material Transfer`；用户界面显示为“物料移动” |
| 客户实际签收/销售出库 | `Delivery Note` | 在途订单必须从 Transit 仓出库 |
| 在途库存导出 | `In Transit Inventory` 报表 | 自定义报表，但数据来源是原生 Stock Entry |

`Customer Shipment`、`Customer Shipment Receipt` 是早期版本留下的自定义 DocType。它们只保留给历史数据查看，不应再用于新订单、报表或日常操作。不要删除这些 DocType 或历史记录，否则旧关联单据可能损坏。

## 6. 自定义字段

字段定义位于 `fmcg_wms/fixtures/custom_field.json`，由 `bench migrate` 同步。

### Sales Order

| 字段名 | 作用 |
| --- | --- |
| `fmcg_delivery_mode` | 必填；值为“当场交付”或“在途交付” |
| `fmcg_transit_warehouse` | 自动记录 Transit 仓；隐藏只读 |
| `fmcg_expected_receipt_date` | 预留字段；隐藏只读 |
| `fmcg_transit_stock_entry` | 自动关联生成的物料移动；隐藏只读 |
| `fmcg_customer_shipment` | 历史兼容字段；新流程不再写入 |

### Stock Entry

| 字段名 | 作用 |
| --- | --- |
| `fmcg_sales_order` | 自动关联来源销售订单；只读，可在列表显示 |
| `fmcg_customer` | 自动关联客户；只读，可在列表显示 |
| `fmcg_expected_receipt_date` | 自动记录订单交货日期；只读 |

### Stock Entry Detail

| 字段名 | 作用 |
| --- | --- |
| `fmcg_sales_order_item` | 自动关联 Sales Order Item；隐藏只读；用于在途报表计算已出库/在途数量 |

## 7. 代码入口

| 文件 | 职责 |
| --- | --- |
| `fmcg_wms/hooks.py` | 挂载表单/列表 JS、销售订单提交事件、销售出库校验事件、字段 fixtures |
| `fmcg_wms/services/sales_order.py` | 两种交付模式、仓库解析、草稿调拨、多次调拨与待送货数量计算 |
| `fmcg_wms/services/delivery.py` | 根据指定订单行数量生成 Delivery Note 草稿或已提交单据 |
| `fmcg_wms/services/stock.py` | 生成原生 Stock Entry 草稿或已提交单据；写入订单、客户、订单行追溯字段 |
| `fmcg_wms/events/sales_order.py` | Sales Order `on_submit` 创建待核准调拨草稿 |
| `fmcg_wms/events/stock_entry.py` | 物料移动核准时校验订单行累计调拨量并记录核准动作 |
| `fmcg_wms/events/delivery_note.py` | 强制在途订单从 Transit 仓出库，并校验签收量不超过已核准调拨量 |
| `fmcg_wms/api/sales_order.py` | 前端调用的白名单接口：默认中心仓、调拨、当场交付、待送货数量和专用送货单 |
| `fmcg_wms/public/js/sales_order.js` | 销售订单默认中心仓、发货菜单、待送货明细、专用送货单入口 |
| `fmcg_wms/public/js/delivery_note.js` | 新建 Delivery Note 时立即预填客户在途仓 |
| `fmcg_wms/public/js/sales_order_list.js` | 列表中为 `per_delivered` 与 `per_billed` 显示进度条和百分比数字 |
| `fmcg_wms/public/css/sales_order_list.css` | 销售订单列表百分比的样式 |
| `fmcg_wms/fmcg_wms/report/in_transit_inventory/` | 在途库存报表，来源为 Stock Entry |

## 8. 关键实现约束

1. 自动调拨只允许已提交的“在途交付”销售订单。
2. 同一销售订单允许多次已提交调拨，但同一时刻只允许一张未提交的调拨草稿；每张新草稿只包含各订单行尚未核准的余额。
3. 旧订单若关联了已提交的 `Customer Shipment`，也禁止新流程重复调拨。
4. 在途销售出库单的仓库必须由服务端 `validate` 再次设置，不能只依赖浏览器 JS。
5. `Stock Entry` 的物料行必须保存 `fmcg_sales_order_item`，否则报表无法准确计算该订单行的已出库数量。
6. 不要把当前业务重新改回“自动创建 Customer Shipment”。用户明确要求使用原生“物料移动”模块作为日常入口。
7. 代码中对 `Delivery Note.remarks` 必须先检查字段是否存在。当前中国版 Delivery Note 不保证有该字段；曾因此出现 `AttributeError`。

## 9. 销售订单列表百分比

版本 `0.4.3` 对销售订单列表的两个标准字段做了显示层增强：

| 标题 | 标准字段 | 显示内容 |
| --- | --- | --- |
| 已出货% | `per_delivered` | 绿色进度条和百分比，例如 `68%` |
| 已开票% | `per_billed` | 绿色进度条和百分比，例如 `100%` |

这里只改变列表渲染，不改变 ERPNext 对出货或开票比例的计算。列表 JS 合并已有 `frappe.listview_settings["Sales Order"]`，不要改为直接覆盖已有设置。

## 10. 在途报表和导出

日常查看单笔调拨：`库存 -> 物料移动`，可直接使用原生筛选、打印和导出 CSV/XLSX。

按在途订单查看：全局搜索 `In Transit Inventory`。报表按 Stock Entry 物料行显示：

- 物料移动
- 客户
- 销售订单
- 调拨日期、在途天数、预计签收日期
- 来源仓、在途仓、物料、单位
- 调拨数量、已出库数量、在途数量

报表的“已出库数量”通过 `Delivery Note Item.so_detail` 与 `Stock Entry Detail.fmcg_sales_order_item` 关联计算。因此，手工创建不带该关联字段的老调拨单不会得到准确的订单行在途余额。

## 11. 发布流程

### 本机

1. 在 `D:\AI\github\fmcg_wms` 修改代码和文档。
2. 运行至少以下静态检查：

   ```powershell
   python -m compileall -q fmcg_wms
   Get-Content fmcg_wms/fixtures/custom_field.json -Raw | ConvertFrom-Json | Out-Null
   ```

3. 使用 GitHub Desktop 查看变更，提交到 `main`，然后 `Push origin`。
4. 不上传 `__pycache__`、`.pyc` 或运行时文件。

### 服务器

以 `frappe` 用户操作，不要使用 `root`：

```bash
cd ~/erpnext-bench/apps/fmcg_wms
git pull upstream main

cd ~/erpnext-bench
bench --site wms.920530.xyz migrate
bench build --app fmcg_wms
bench --site wms.920530.xyz clear-cache
bench restart
bench --site wms.920530.xyz list-apps
```

最后必须确认 `fmcg_wms` 显示预期版本号。涉及 JavaScript 或 CSS 的任何修改都必须执行 `bench build`，并要求浏览器使用 `Ctrl + F5` 强制刷新。

升级前建议备份：

```bash
bench --site wms.920530.xyz backup --with-files
```

## 12. 每次发布后的验收清单

请用新的测试销售订单验证，不要用已经完成或已取消的历史单据。

1. 新建销售订单，确认默认出货仓为中心仓。
2. 选择“在途交付”并提交。
3. 确认系统打开一张草稿 `MAT-STE-...` 物料移动，且中心仓和客户在途仓库存均未变化。
4. 将草稿行改为部分数量，核准并提交；确认中心仓只减少本次数量、客户在途仓只增加本次数量。
5. 回到订单，从“发货”创建第二张调拨，确认默认数量只包含尚未核准的余额；再次核准部分数量。
6. 在订单“发货”菜单打开“待送货明细”，确认每行的本次可送数量等于已核准调拨减已送货；未调拨数量单独显示。
7. 从订单“创建本次送货单”，确认草稿只带入本次可送的商品和数量，表头和每个明细行仓库均为客户在途仓；将草稿数量上调后提交必须被阻止。
7. 提交销售出库单，确认客户在途仓减少，销售订单 `per_delivered` 增加。
8. 回到销售订单列表，确认“已出货%”和“已开票%”均显示数字百分比。
9. 打开 `In Transit Inventory`，确认每张已核准物料移动可被检索和导出，已签收数量只从最早未结清调拨开始扣减。

## 13. 已知限制和建议的后续方向

| 项目 | 当前状态 | 后续处理建议 |
| --- | --- | --- |
| 多个 Transit 仓 | 不支持自动选择 | 增加公司配置或客户维度的在途仓映射后再实现 |
| 部分/分车发运 | 支持多次草稿调拨和逐次核准 | 每次仅允许一张待核准草稿；销售出库不得超过已核准且未签收数量 |
| 退货 | 可使用原生物料移动从在途仓退回中心仓 | 若需要按订单追踪退货，增加退货 Stock Entry 与 Sales Order Item 的关联字段 |
| 批次/序列号 | 仅在来源数据存在时尝试复制追溯字段 | 上线前需用真实批次、序列号物料做专项测试 |
| 老 Customer Shipment 数据 | 保留，只供历史查看 | 不要删除；若要迁移展示，先制定数据迁移和回滚方案 |
| 自动化测试 | 当前本机未配置 pytest/Frappe 集成环境 | 建议在服务器测试站建立 Frappe 集成测试后再做高风险改动 |

## 14. 给下一位 AI 的工作规则

1. 先阅读本文件、`README.md` 和 `docs/deployment.md`，再修改代码。
2. 先确认服务器 `bench --site wms.920530.xyz list-apps` 的应用版本，避免基于错误版本排查。
3. 任何库存流转改动都必须同时检查：Sales Order、Stock Entry、Delivery Note、Stock Ledger 和在途报表。
4. 前端方便性可以增加，但库存仓库归属必须由 Python 服务端校验保证。
5. 每次修改版本号时，同时更新：`fmcg_wms/__init__.py`、`fmcg_wms/hooks.py`、`pyproject.toml`、`setup.py`。
6. 不要通过删除历史单据或直接改数据库来“修复”库存差异；先识别关联的 Stock Entry、Delivery Note、GL Entry，再走可审计的取消/冲销流程。
7. 变更完成后更新本交接文档的版本、日期、行为说明和已知限制。
