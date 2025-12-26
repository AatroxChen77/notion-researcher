# **基于计算机视觉视角的空间跨组学预测方法深度调研报告：架构迁移与前沿探索**

## **1. 执行摘要与研究背景**

随着空间生物学技术的飞速发展，空间转录组学（Spatial Transcriptomics, ST）与空间蛋白质组学已成为解析复杂组织微环境（TME）的“新显微镜”。

然而，受限于测序深度、捕获效率及昂贵的实验成本，现有的空间组学数据普遍面临三大挑战：

1. **数据稀疏性（Dropout）**、
2. **空间分辨率不足（非单细胞精度）**
3. **多中心批次效应（Batch Effect）**。

与此同时，计算机视觉（CV）领域在2022至2025年间经历了从卷积神经网络（CNN）到Vision Transformers (ViT)，再到状态空间模型（State Space Models, SSM/**Mamba**）的范式转移，特别是在高光谱图像重建、图像修复及域适应回归任务上取得了突破性进展。

本报告旨在建立一个跨学科的理论与技术迁移框架。基于**“空间组学数据即高维多通道图像（Pixel ≈ Cell/Bin, Channel ≈ Gene）”**的核心假设，我们将深入剖析CV顶会（CVPR, ICCV, ECCV, NeurIPS）中的前沿算法，挖掘其解决生物学问题的潜力。报告将重点论证如何利用**光谱-空间注意力机制**解决基因共表达建模，利用**Mamba/VMamba**打破高维数据的计算瓶颈，利用**掩码图像建模（MIM）**实现表达量插补，以及利用**逆Gram矩阵对齐**实现回归任务的域适应，从而构建下一代高精度的空间跨组学预测系统。

## **2. 问题形式化：从高光谱成像到空间组学**

在深入技术细节之前，必须明确CV任务与空间组学任务的同构性。

### **2.1 数据结构的同构映射**

空间转录组数据通常表示为表达矩阵 $X \in \mathbb{R}^{N \times G}$ 和空间坐标 $C \in \mathbb{R}^{N \times 2}$，其中 $N$ 为捕获点数，$G$ 为基因数（通常 $>20,000$）。将其网格化后，可视为张量 $\mathcal{T} \in \mathbb{R}^{H \times W \times G}$。这与高光谱图像（Hyperspectral Image, HSI）的结构 $\mathcal{T}_{HSI} \in \mathbb{R}^{H \times W \times \lambda}$ 完全一致，其中 $\lambda$ 为光谱波段数。

- **通道相关性（Channel Correlation）：** 在HSI中，相邻波段及特定波段组合反映物质成分；在ST中，基因通道间的相关性对应**基因调控网络（GRN）**。
- **空间相关性（Spatial Correlation）：** HSI的纹理反映地物形态；ST的空间分布反映**组织形态学**及**细胞通讯**。
- **任务映射：**

- 由低分辨率/稀疏ST预测高分辨率ST $\rightarrow$ **高光谱超分辨率（Hyperspectral Super-Resolution）**。
- 由H&E染色图预测ST $\rightarrow$ **跨模态引导超分（Guided Super-Resolution）** 或 **模态迁移（Image-to-Image Translation）**。
- 填补未测到的基因 $\rightarrow$ **图像修复（Inpainting / MIM）**。

### **2.2 核心挑战：维度的诅咒**

传统CV模型（如ResNet, UNet）通常处理3通道（RGB）图像。当通道数扩展至数千甚至数万时，标准卷积核的参数量将呈线性爆炸，而基于Self-Attention的Transformer模型则面临序列长度的二次方复杂度 $O((HW)^2)$ 瓶颈。因此，本调研将特别关注**线性复杂度骨干网络（Linear Complexity Backbones）**和**通道注意力（Channel Attention）**的最新进展。

## **3. 高光谱图像重建与通道相关性建模**

在CVPR 2024和ACCV 2024中，高光谱图像重建的研究重心已从单纯的空间特征提取转向深度的**光谱-空间联合建模**，这为解决空间组学中的“基因互作”提供了直接的迁移思路。

### **3.1 累积注意力机制：SPECAT**

传统的Self-Attention机制在处理高光谱数据时，往往难以捕捉光谱维度上的局部突变特征（Non-local mutation features）。在生物学语境下，这些“突变”可能对应着决定细胞命运的关键转录因子或稀有细胞类型的特异性标记，它们在统计上被大量的管家基因信号所掩盖。

**CVPR 2024** 提出的 **SPECAT (SPatial-spEctral Cumulative-Attention Transformer)** 1 引入了一种创新的**累积注意力块（Cumulative-Attention Block, CAB）**。

- **核心思想：** 不同于一次性计算全局注意力图，CAB采用分层累积的方式聚合特征。它设计了一个高效的层次化框架，能够在保留非局部空间-光谱细节的同时，通过累积效应增强微弱的光谱特征。
- **双域损失函数（Dual-domain Loss Function, DLF）：** SPECAT不仅在像素空间计算损失，还引入了投影对象（Projection-object）约束，即在频率域或特征投影空间施加约束。
- **迁移灵感：** 在训练空间组学预测模型时，仅使用MSE（均方误差）往往导致预测结果过于平滑，丢失极值（高表达基因）。引入类似DLF的机制，强制模型在**基因特征空间（Gene Eigenspace）或傅里叶域**保持一致性，有助于保留组织切片中的高频边缘信息（如肿瘤边界）。

### **3.2 稀疏光谱Transformer：SSTHyper**

针对高光谱数据存在大量冗余波段的问题，**ACCV 2024** 的 **SSTHyper (Sparse Spectral Transformer)** 3 提出了基于稀疏性的解决方案。

- **核心思想：** 并非所有光谱波段都对重建有贡献。SSTHyper通过学习一个稀疏掩码或稀疏注意力矩阵，自动筛选出最具信息量的波段组合进行交互建模。
- **迁移灵感：** 基因表达矩阵具有显著的低秩性（Low-rankness）。将SSTHyper的稀疏注意力机制迁移到ST预测中，实际上是在模型内部进行**特征基因选择（Feature Selection）**，这不仅降低了计算量，还能使得模型学到的潜在空间（Latent Space）更具生物学解释性（即对应于特定的Gene Module）。

### **3.3 卷积光谱自注意力：TCSSA**

对于计算资源受限的场景，**TCSSA (Transformer with Convolutional Spectral Self-Attention)** 4 提供了一种轻量级思路。

- **架构细节：** 该模型由CNN-Transformer编码器和解码器组成。核心组件**CSSA（Convolutional Spectral Self-Attention）**巧妙地结合了卷积的局部归纳偏置（Inductive Bias）和Transformer的全局建模能力。具体而言，它利用卷积提取空间上的局部纹理（对应细胞形态），同时利用Self-Attention在通道维度上建模全局光谱依赖（对应全基因组的调控网络）。
- **性能权衡：** 实验证明，CSSA在GF5（遥感）和CAVE（自然图像）数据集上实现了重建性能与计算复杂度的平衡 4。这对于开发可部署在本地服务器上的病理分析软件极具参考价值。

## **4. 突破计算瓶颈：State Space Models (Mamba) 的崛起**

如果说Transformer解决了长距离依赖问题，那么**State Space Models (SSM)** 则解决了Transformer在长序列上的计算效率问题。**CVPR 2024, ECCV 2024, CVPR 2025** 见证了Mamba架构在视觉任务中的爆发，这对于处理“Gigapixel”级别的全切片病理图像（WSI）和高维空间组学数据是革命性的。

### **4.1 Mamba的核心优势：线性复杂度**

Mamba基于结构化状态空间模型（S4），核心在于选择性扫描机制（Selective Scan, S6）。其离散化状态方程可以表示为：

$$h_t = \bar{A} h_{t-1} + \bar{B} x_t$$

$$y_t = C h_t$$

与Transformer需要存储 $N \times N$ 的注意力矩阵不同，Mamba通过递归状态 $h_t$ 压缩历史信息，实现了 $O(N)$ 的线性复杂度 5。对于包含数万个基因通道或数百万个像素的空间组学数据，这意味着可以在不进行切块（Patching）的情况下处理更大的上下文窗口。

### **4.2 2D扫描策略：VMamba 与 Vision Mamba**

由于SSM本质上是1D序列模型，如何处理2D图像结构是关键。

- **Vision Mamba (Vim)** 7：引入双向扫描（Bidirectional Scan），分别从前向后和从后向前遍历图像序列，以捕捉上下文。
- **VMamba** 9：提出了**SS2D（2D Selective Scan）**模块，采用四向扫描策略（左上$\to$右下，右下$\to$左上，右上$\to$左下，左下$\to$右上），确保每个像素都能感知到来自四个方向的全局信息。
- **迁移灵感：** 空间组学数据中的细胞间通讯是全方位的。VMamba的四向扫描机制能更好地模拟这种非因果（Non-causal）的生物信号传递，比单向扫描更符合生物学直觉。

### **4.3 空间-光谱联合Mamba：HyperSMamba 与 SSUM**

针对高光谱数据的特殊性，研究者提出了**HyperSMamba** 10 和 **SSUM (Spatial-Spectral Unified Mamba)** 9。这是目前最契合用户需求的架构。

- **双分支架构（Dual-Branch）：** 这些模型通常包含两个并行分支：

1. **Spatial Mamba Branch：** 使用SS2D模块扫描像素空间，提取组织纹理特征。
2. **Spectral Mamba Branch：** 将光谱通道视为序列进行扫描，提取基因间的长程依赖。

- **自适应融合（Adaptive Fusion）：** 引入**空间-光谱融合模块（Spatial-Spectral Fusion Module）**，通过注意力机制动态调整两个分支的权重。
- **最近邻光谱融合（NSF）与子光谱扫描（SS）：** SSUM引入了NSF策略来减轻空间变异性（同物异谱）的干扰，并设计了子光谱扫描机制以增强对微细光谱特征的感知 14。
- **迁移灵感：** 直接采用HyperSMamba架构作为骨干网。在空间组学中，“同物异谱”现象非常普遍（同种细胞在不同细胞周期或微环境下表达谱不同）。NSF策略可以作为一种**生物学噪声抑制机制**，提高细胞类型识别的鲁棒性。

### **4.4 图像恢复专用Mamba：MambaIR 与 MambaIRv2**

针对图像超分和去噪任务（Image Restoration），**ECCV 2024** 的 **MambaIR** 15 和 **CVPR 2025** 的 **MambaIRv2** 17 做出了重要改进。

- **MambaIR：** 提出了**残差状态空间块（RSSB）**，在SSM中引入了**通道注意力（Channel Attention）**。这一设计直接解决了原始Mamba在低级视觉任务中存在的“通道冗余”问题。在组学数据中，这意味着模型可以自动抑制技术噪声通道（无效基因），增强信号通道。
- **MambaIRv2：** 针对Mamba的因果性（Causality）限制（即像素只能看到之前的像素），提出了**注意力状态空间方程（Attentive State-Space Equation）和语义引导邻域（Semantic Guided Neighboring, SGN）**。

- **SGN机制：** 这是一个极其深刻的创新。它不再按照物理坐标扫描图像，而是先根据语义相似性重新排列像素，形成一个新的序列，再进行SSM扫描。
- **迁移灵感（SGN的生物学意义）：** 在空间转录组中，物理上相邻的细胞未必是功能上最相关的（例如淋巴细胞可能散布在肿瘤间质中）。利用SGN，我们可以先基于H&E形态学特征对细胞进行聚类排序，让Mamba在“语义序列”上进行扫描。这将使得状态 $h_t$ 能够跨越物理距离，在同类细胞群体内部传递信息，极大地增强了模型对**远距离细胞互作**的建模能力。

## **5. 解决数据缺失：掩码图像建模 (MIM) 与 修复**

空间组学的Dropout现象（零膨胀）是数据分析的主要障碍。CV领域的**掩码图像建模（Masked Image Modeling, MIM）**提供了一种自监督的解决思路。

### **5.1 SimMIM 与 SpectralMAE**

**SimMIM** 20 证明了简单的随机掩码（Random Masking）配合轻量级解码器即可学习到强大的表征。而 **SpectralMAE** 21 将这一思想扩展到了光谱域。

- **双重掩码策略：** SpectralMAE不仅在空间上掩盖Patch，还在光谱维度上随机Drop掉部分波段。
- **迁移灵感：** 这是一个完美的预训练任务（Pre-text Task）。可以在大规模无标注的空间组学数据上训练一个SpectralMAE，任务是恢复被Mask掉的基因表达值。这不仅教会模型理解组织结构，更教会模型理解基因共表达模式。在推理阶段，该模型即可直接用于**数据插补（Imputation）**，填补因技术原因丢失的基因信号。

### **5.2 RAM: Restore Anything with Masks**

**ECCV 2024** 的 **RAM (Restore Anything with Masks)** 22 提出了一种针对“盲图像恢复”的通用框架。

- **核心创新：掩码属性传导（Mask Attribute Conductance, MAC）。** 这是一个层级重要性评估算法。RAM通过计算每一层对掩码恢复任务的贡献度（Conductance），来识别出网络中哪些层是负责“内容恢复”的关键层。
- **迁移灵感：** 在跨批次或跨组织预测时，我们往往不希望重训整个网络。利用MAC算法，我们可以精准定位那些负责“基因表达模式重建”的关键层进行微调（Fine-tuning），而冻结那些负责提取通用纹理特征的层。这不仅提高了训练效率，还有效防止了在小样本数据上的过拟合。

### **5.3 BiMAE：双模态掩码自编码器**

**BiMAE** 24 探索了利用一种模态（如RGB图像）来辅助重建另一种模态（如高光谱）的掩码区域。这直接对应于**H&E引导的空间转录组插补**。通过联合训练，H&E图像的形态学特征可以作为先验（Prior），指导稀疏基因数据的致密化。

## **6. 消除批次效应：回归任务的域适应 (UDA)**

这是用户查询中极具挑战性的一点。传统的UDA方法（如DANN, MMD）多用于分类任务（对齐类别分布），而基因预测是**回归任务（Pixel-wise Regression）**。CVPR 2023/2024 的 **DARE-GRAM** 提供了一个数学上优雅的解法。

### **6.1 DARE-GRAM：对齐逆Gram矩阵**

**DARE-GRAM (Unsupervised Domain Adaptation Regression by Aligning Inverse Gram Matrices)** 25 提出从回归分析的闭式解（Ordinary Least Squares, OLS）出发。

- **理论基础：** 在线性回归 $y = X\beta$ 中，最优解 $\hat{\beta} = (X^TX)^{-1}X^Ty$ 依赖于特征协方差矩阵（Gram Matrix, $G=X^TX$）的逆。
- **Gram矩阵的生物学含义：** 在空间组学中，特征矩阵 $X$ 的Gram矩阵 $X^TX$ 实际上编码了特征之间的二阶相关性，即**基因-基因相关性矩阵（Gene Correlation Matrix）**或**基因调控网络（GRN）**的拓扑结构。
- **方法论：** DARE-GRAM 提出，不同批次的数据虽然表达量分布不同（Scale Shift），但其内在的物理/生物学规律（即基因调控关系）应当是一致的。因此，通过在潜在空间对齐源域和目标域的**逆Gram矩阵（$(X^TX)^{-1}$）**，实际上是在强制两个域共享相同的回归几何结构（Regression Geometry）。
- **迁移灵感：** 这是一个处理批次效应的“白盒”思路。在训练预测模型时，加入一项损失函数，最小化源切片和目标切片特征的逆Gram矩阵距离。这能确保模型预测出的基因表达不仅数值准确，而且保留了正确的基因互作网络结构，防止出现“生物学上不可能”的表达组合。

### **6.2 风格迁移与神经预设 (Neural Preset)**

对于H&E图像本身的色差（染色深浅、扫描仪差异），**Neural Preset** 26 提供了一种优于传统GAN的方法。它通过学习一个确定性的颜色映射矩阵（Deterministic Neural Color Mapping, DNCM），将图像归一化到标准颜色空间，同时避免了GAN生成图像常见的伪影和模糊。作为预处理步骤，这对于保证下游回归模型的稳定性至关重要。

## **7. 多模态融合与引导超分**

如何利用高分辨率的H&E图像（Sub-micron）引导低分辨率ST数据（10-50$\mu m$）的超分？

### **7.1 Ref-Diff：基于参考的扩散模型**

**CVPR 2024** 的 **Ref-Diff** 27 针对参考图像超分（RefSR）问题，提出了**变化感知扩散模型（Change-Aware Diffusion Model）**。

- **核心思想：** 传统的RefSR假设参考图（Reference）与低分图（Input）内容完全一致。但在ST中，H&E图像与ST数据可能存在微小的非刚性形变，或者H&E反映的形态与基因表达之间存在非线性映射（变化）。Ref-Diff引入了**变化先验（Change Priors）**，解耦了语义引导的去噪过程和纹理迁移过程。
- **迁移灵感：** 将H&E作为Reference，ST作为Input。Ref-Diff架构允许模型在利用H&E提供的高频纹理细节（细胞边界）的同时，容忍两者在信息含量上的不完全对齐（例如某些形态学结构并不对应特定的基因表达），从而生成既清晰又真实的超分图谱。

### **7.2 iRAG：图像检索增强生成**

**ICCV 2025** (Preview) 的 **iRAG (Image-based Retrieval-Augmented Generation)** 29 将大语言模型中的RAG概念引入底层视觉。

- **核心思想：** 不仅依赖模型内部的参数记忆，还从外部数据库中检索相似的高清Patch作为参考。
- **迁移灵感：** 这是一个极具前瞻性的方向。我们可以构建一个**“组织图谱数据库”（如Human Cell Atlas）**。当模型需要预测某块组织的基因表达时，iRAG可以先从图谱库中检索出形态相似的单细胞测序数据作为Reference。这种**基于知识库的超分（Knowledge-Based Super-Resolution）**将极大地提高预测的生物学可信度，特别是对于罕见组织结构的处理。

### **7.3 SinSR：单步扩散加速**

针对扩散模型推理慢的问题，**SinSR** 31 实现了单步（Single-step）超分，这对于处理吉字节级别的全切片数据至关重要，使得临床实时病理辅助诊断成为可能。

## **8. 总结与建议架构：OmicsMamba-SR**

综合上述调研，我们构想了一个名为 **OmicsMamba-SR** 的端到端空间跨组学预测框架，以此作为本报告的最终产出。

### **8.1 建议架构图谱**

| **模块**       | **CV源头技术 (2022-2025)**        | **迁移后的生物学功能** | **核心优势**                                                 |
| -------------- | --------------------------------- | ---------------------- | ------------------------------------------------------------ |
| **预处理**     | **Neural Preset** 26              | H&E染色归一化          | 消除染色批次效应，保留解剖结构                               |
| **骨干网络**   | **MambaIRv2** 17 + **SSTHyper** 3 | 空间-光谱双流特征提取  | **SGN**机制实现基于细胞类型的非局部交互；线性复杂度支持全切片输入 |
| **注意力机制** | **SPECAT** (Cumulative Attn) 1    | 捕捉稀有细胞/基因信号  | 累积注意力防止微弱的“突变特征”被平滑                         |
| **域适应**     | **DARE-GRAM** 25                  | 跨切片/跨病人回归校准  | 对齐**逆Gram矩阵**以保持基因调控网络的一致性                 |
| **数据增强**   | **SpectralMAE** 21                | 自监督基因插补         | 解决Dropout问题，学习基因共表达流形                          |
| **生成解码**   | **Ref-Diff** 27 / **iRAG** 29     | H&E引导的超分辨率生成  | 利用H&E纹理或外部图谱库知识，生成单细胞级表达谱              |

### **8.2 核心结论**

1. **拥抱线性复杂度：** 鉴于空间组学数据的海量通道和吉像素特性，传统的ViT已不再适用。**Mamba/VMamba** 及其变体（特别是引入了SGN和通道注意力的MambaIRv2）是当前最值得投入的新一代骨干网络。
2. **回归任务的域适应是关键：** 简单的分布对齐（如对抗学习）可能破坏基因间的精细相关性。**DARE-GRAM** 提供的二阶统计量（Gram矩阵）对齐策略，为回归任务提供了一个保结构（Structure-Preserving）的解决方案。
3. **从“预测”走向“检索与生成”：** iRAG的出现提示我们，未来的预测模型不应是封闭的，而应是开放的，能够利用现有的海量单细胞图谱知识库来增强预测的准确性和生物学合理性。

本报告所调研的技术路径，为构建高精度、高通量、抗干扰的空间跨组学预测平台提供了坚实的理论支撑和具体的工程蓝图。

#### **引用的著作**

1. SPECAT: SPatial-spEctral Cumulative-Attention ... - CVF Open Access, 访问时间为 十二月 25, 2025， https://openaccess.thecvf.com/content/CVPR2024/html/Yao_SPECAT_SPatial-spEctral_Cumulative-Attention_Transformer_for_High-Resolution_Hyperspectral_Image_Reconstruction_CVPR_2024_paper.html
2. SPECAT: SPatial-spEctral Cumulative-Attention Transformer for High-Resolution Hyperspectral Image Reconstruction - CVF Open Access, 访问时间为 十二月 25, 2025， https://openaccess.thecvf.com/content/CVPR2024/papers/Yao_SPECAT_SPatial-spEctral_Cumulative-Attention_Transformer_for_High-Resolution_Hyperspectral_Image_Reconstruction_CVPR_2024_paper.pdf
3. SSTHyper: Sparse Spectral Transformer for Hyperspectral Image Reconstruction - CVF Open Access, 访问时间为 十二月 25, 2025， https://openaccess.thecvf.com/content/ACCV2024/papers/Xu_SSTHyper_Sparse_Spectral_Transformer_for_Hyperspectral_Image_Reconstruction_ACCV_2024_paper.pdf
4. Spectral Superresolution Using Transformer with Convolutional Spectral Self-Attention - MDPI, 访问时间为 十二月 25, 2025， https://www.mdpi.com/2072-4292/16/10/1688
5. Ruixxxx/Awesome-Vision-Mamba-Models: [Official Repo] Visual Mamba: A Survey and New Outlooks - GitHub, 访问时间为 十二月 25, 2025， https://github.com/Ruixxxx/Awesome-Vision-Mamba-Models
6. VMRNN: Integrating Vision Mamba and LSTM for Efficient and Accurate Spatiotemporal Forecasting - CVF Open Access, 访问时间为 十二月 25, 2025， https://openaccess.thecvf.com/content/CVPR2024W/PRECOGNITION/papers/Tang_VMRNN_Integrating_Vision_Mamba_and_LSTM_for_Efficient_and_Accurate_CVPRW_2024_paper.pdf
7. MambaVision: A Hybrid Mamba-Transformer Vision Backbone - CVF Open Access, 访问时间为 十二月 25, 2025， https://openaccess.thecvf.com/content/CVPR2025/papers/Hatamizadeh_MambaVision_A_Hybrid_Mamba-Transformer_Vision_Backbone_CVPR_2025_paper.pdf
8. GMSR:Gradient-Guided Mamba for Spectral Reconstruction from RGB Images - arXiv, 访问时间为 十二月 25, 2025， https://arxiv.org/html/2405.07777v1
9. SSUM: Spatial–Spectral Unified Mamba for Hyperspectral Image Classification - MDPI, 访问时间为 十二月 25, 2025， https://www.mdpi.com/2072-4292/16/24/4653
10. HyperSMamba: A Lightweight Mamba for Efficient Hyperspectral Image Classification, 访问时间为 十二月 25, 2025， https://www.mdpi.com/2072-4292/17/12/2008
11. MambaHSI: Spatial-Spectral Mamba for Hyperspectral Image Classification - arXiv, 访问时间为 十二月 25, 2025， https://arxiv.org/html/2501.04944v1
12. The overall architecture of HyperSMamba. | Download Scientific Diagram - ResearchGate, 访问时间为 十二月 25, 2025， https://www.researchgate.net/figure/The-overall-architecture-of-HyperSMamba_fig1_392608351
13. A Spatial-Spectral Efficient Method of Mamba for Hyperspectral Image Classification, 访问时间为 十二月 25, 2025， https://www.researchgate.net/publication/397976574_A_Spatial-Spectral_Efficient_Method_of_Mamba_for_Hyperspectral_Image_Classification
14. (PDF) SSUM: Spatial–Spectral Unified Mamba for Hyperspectral Image Classification, 访问时间为 十二月 25, 2025， https://www.researchgate.net/publication/386998632_SSUM_Spatial-Spectral_Unified_Mamba_for_Hyperspectral_Image_Classification
15. MambaIR: A Simple Baseline for Image Restoration with State-Space Model - arXiv, 访问时间为 十二月 25, 2025， https://arxiv.org/html/2402.15648v3
16. MambaIR: A Simple Baseline for Image Restoration with State-Space Model - European Computer Vision Association, 访问时间为 十二月 25, 2025， https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/02740.pdf
17. MambaIRv2: Attentive State Space Restoration - CVF Open Access, 访问时间为 十二月 25, 2025， https://openaccess.thecvf.com/content/CVPR2025/papers/Guo_MambaIRv2_Attentive_State_Space_Restoration_CVPR_2025_paper.pdf
18. MambaIRv2: Attentive State Space Restoration - arXiv, 访问时间为 十二月 25, 2025， https://arxiv.org/html/2411.15269v1
19. MambaIRv2: Attentive State Space Restoration - arXiv, 访问时间为 十二月 25, 2025， https://arxiv.org/html/2411.15269v2
20. SimMIM: A Simple Framework for Masked Image Modeling - CVF Open Access, 访问时间为 十二月 25, 2025， https://openaccess.thecvf.com/content/CVPR2022/papers/Xie_SimMIM_A_Simple_Framework_for_Masked_Image_Modeling_CVPR_2022_paper.pdf
21. SpectralMAE: Spectral Masked Autoencoder for Hyperspectral Remote Sensing Image Reconstruction - PMC - NIH, 访问时间为 十二月 25, 2025， https://pmc.ncbi.nlm.nih.gov/articles/PMC10099040/
22. Restore Anything with Masks: Leveraging Mask Image Modeling for Blind All-in-One Image Restoration - European Computer Vision Association, 访问时间为 十二月 25, 2025， https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/06185.pdf
23. Restore Anything with Masks: Leveraging Mask Image Modeling for Blind All-in-One Image Restoration - arXiv, 访问时间为 十二月 25, 2025， https://arxiv.org/html/2409.19403v1
24. BiMAE - A Bimodal Masked Autoencoder Architecture for Single-Label Hyperspectral Image Classification - CVF Open Access, 访问时间为 十二月 25, 2025， https://openaccess.thecvf.com/content/CVPR2024W/PBVS/papers/Kukushkin_BiMAE_-_A_Bimodal_Masked_Autoencoder_Architecture_for_Single-Label_Hyperspectral_CVPRW_2024_paper.pdf
25. Unsupervised Domain Adaptation Regression by Aligning Inverse Gram Matrices - CVF Open Access, 访问时间为 十二月 25, 2025， https://openaccess.thecvf.com/content/CVPR2023/papers/Nejjar_DARE-GRAM_Unsupervised_Domain_Adaptation_Regression_by_Aligning_Inverse_Gram_Matrices_CVPR_2023_paper.pdf
26. Neural Preset for Color Style Transfer | CVF Open Access, 访问时间为 十二月 25, 2025， https://openaccess.thecvf.com/content/CVPR2023/papers/Ke_Neural_Preset_for_Color_Style_Transfer_CVPR_2023_paper.pdf
27. CVPR 2024 Open Access Repository, 访问时间为 十二月 25, 2025， https://openaccess.thecvf.com/content/CVPR2024/html/Dong_Building_Bridges_across_Spatial_and_Temporal_Resolutions_Reference-Based_Super-Resolution_via_CVPR_2024_paper.html
28. [Quick Review] Building Bridges Across Spatial and Temporal Resolutions: Reference-Based Super-Resolution via Change Priors and Conditional Diffusion Model - Liner, 访问时间为 十二月 25, 2025， https://liner.com/review/building-bridges-across-spatial-and-temporal-resolutions-referencebased-superresolution-via
29. Reference-based Super-Resolution via Image-based Retrieval-Augmented Generation Diffusion | Cool Papers - Immersive Paper Discovery, 访问时间为 十二月 25, 2025， https://papers.cool/venue/Lee_Reference-based_Super-Resolution_via_Image-based_Retrieval-Augmented_Generation_Diffusion@ICCV2025@CVF
30. ICCV Poster Reference-based Super-Resolution via Image-based Retrieval-Augmented Generation Diffusion - The Computer Vision Foundation, 访问时间为 十二月 25, 2025， https://iccv.thecvf.com/virtual/2025/poster/2199
31. SinSR: Diffusion-Based Image Super-Resolution in a Single Step - CVPR 2024 Open Access Repository - The Computer Vision Foundation, 访问时间为 十二月 25, 2025， https://openaccess.thecvf.com/content/CVPR2024/html/Wang_SinSR_Diffusion-Based_Image_Super-Resolution_in_a_Single_Step_CVPR_2024_paper.html