"""
GPT model:
- the initial stem consists of a combination of token encoding and a positional encoding
- the meat of it is a uniform sequence of Transformer blocks
    - each Transformer is a sequential combination of a 1-hidden-layer MLP block and a self-attention block
    - all blocks feed into a central residual pathway similar to resnets
- the final decoder is a linear projection into a vanilla Softmax classifier
"""

import math
import torch
import torch.nn as nn
from torch.nn import functional as F
from easydict import EasyDict

def get_subsequent_mask(seq_len, sliding_windown_size):
    """ For masking out the subsequent info. """
    mask = torch.ones((seq_len, seq_len)).float()
    mask = torch.triu(mask, diagonal=-sliding_windown_size)
    mask = torch.tril(mask, diagonal=sliding_windown_size)
    return mask #.bool()

class MaskAttention(nn.Module):
    """
    A vanilla multi-head masked self-attention layer with a projection at the end.
    It is possible to use torch.nn.MultiheadAttention here but I am including an
    explicit implementation here to show that there is nothing too scary here.
    """

    def __init__(self, config):
        super().__init__()
        assert config.n_embd % config.n_head == 0
        self.key = nn.Linear(config.n_embd, config.n_embd)
        self.query = nn.Linear(config.n_embd, config.n_embd)
        self.value = nn.Linear(config.n_embd, config.n_embd)
        self.attn_drop = nn.Dropout(config.attn_pdrop)
        self.resid_drop = nn.Dropout(config.resid_pdrop)
        self.proj = nn.Linear(config.n_embd, config.n_embd)

        self.register_buffer("mask", get_subsequent_mask((config.block_size + config.window_size//2 * 2) * config.downsample_rate, config.window_size//2 * config.downsample_rate)
                                     [None, None])
        self.n_head = config.n_head

    def forward(self, x, layer_past=None):
        B, T, C = x.size()  # T = 3*t (music up down)

        k = self.key(x).view(B, T, self.n_head, C // self.n_head).transpose(1, 2) # (B, nh, T, hs)
        q = self.query(x).view(B, T, self.n_head, C // self.n_head).transpose(1, 2) # (B, nh, T, hs)
        v = self.value(x).view(B, T, self.n_head, C // self.n_head).transpose(1, 2) # (B, nh, T, hs)
        t = T 
        att = (q @ k.transpose(-2, -1)) * (1.0 / math.sqrt(k.size(-1)))
        att = att.masked_fill(self.mask[:,:,:t,:t] == 0, float('-inf'))
        att = F.softmax(att, dim=-1)
        att = self.attn_drop(att)
        y = att @ v # (B, nh, T, T) x (B, nh, T, hs) -> (B, nh, T, hs)
        y = y.transpose(1, 2).contiguous().view(B, T, C) # re-assemble all head outputs side by side

        y = self.resid_drop(self.proj(y))
        return y

class MusicBlock(nn.Module):
    """ an unassuming Transformer block """

    def __init__(self, config):
        super().__init__()
        self.ln1 = nn.LayerNorm(config.n_embd)
        self.ln2 = nn.LayerNorm(config.n_embd)
        self.attn = MaskAttention(config)
        self.mlp = nn.Sequential(
            nn.Linear(config.n_embd, 4 * config.n_embd),
            nn.GELU(),
            nn.Linear(4 * config.n_embd, config.n_embd),
            nn.Dropout(config.resid_pdrop),
        )

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x


class MusicTrans(nn.Module):
    """ mix up the neiboring music features before auto-regressively inference"""
    def __init__(self, config):
        super().__init__()

        # # input embedding stem
        # self.requires_head = config.requires_head
        # self.requires_tail = config.requires_tail

        # if config.requires_head:
        # dance_
        config = EasyDict(config)
        self.config = config

        self.pos_emb = nn.Parameter(torch.zeros(1, (config.block_size + config.window_size//2*2)*config.downsample_rate, config.n_embd))
        self.cond_emb = nn.Linear(config.n_music, config.n_embd)
        self.drop = nn.Dropout(config.embd_pdrop)
        # transformer
        self.blocks = nn.Sequential(*[MusicBlock(config) for _ in range(config.n_layer)])

        self.downsample = nn.Linear(config.n_embd * config.downsample_rate, config.n_embd)
        # decoder head
        # self.ln_f = nn.LayerNorm(config.n_embd)

        self.block_size = config.block_size
        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            # module.weight.data.uniform_(math.sqrt(6.0/sum(module.weight.size())))
            module.weight.data.normal_(mean=0.0, std=0.02)
            if isinstance(module, nn.Linear) and module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.LayerNorm):
            module.bias.data.zero_()
            module.weight.data.fill_(1.0)

    def forward(self, music):
        # print(music.size(), flush=True)
        b, t, c = music.size()
        assert t <= (self.config.block_size + self.config.window_size//2 * 2) * self.config.downsample_rate, "Cannot forward, model block size is exhausted."
      
        # forward the GPT model
        # if self.requires_head:
        # token_embeddings_up = self.tok_emb_up(idx_up) # each index maps to a (learnable) vector
        # token_embeddings_down = self.tok_emb_down(idx_down) # each index maps to a (learnable) vector
        # print('Line 143 music size', music.size())
        token_embeddings = self.cond_emb(music)

        x = self.drop(token_embeddings)
        x = self.blocks(x)

        # print('Line 149 x size', x.size())

        xd = x[:, self.config.window_size//2 * self.config.downsample_rate:-(self.config.window_size//2) * self.config.downsample_rate, :].contiguous()
        
        # print('L153 xd size', xd.size())
        b, t, c = xd.size()
        x = self.downsample(xd.view(b, t // self.config.downsample_rate, c * self.config.downsample_rate))
        # print('L156 x size', x.size())
        # x = self.ln_f(x)

        return x


class CrossCondGPT2MWAC(nn.Module):
    """  the full GPT language model, with a context size of block_size """

    def __init__(self, config):
        super().__init__()
        self.music_trans = MusicTrans(config.music_trans)
        self.gpt_base = CrossCondGPTBase(config.base)
        self.gpt_head = CrossCondGPTHead(config.head)
        self.critic_net = CrossCondGPTHead(config.critic_net)
        
        # self.down_half_gpt = CrossCondGPTHead(config.down_half_gpt)
        # if hasattr(config, 'critic_net'):
        #     self.critic_net = CrossCondGPTHead(config.critic_net)
        self.block_size = config.block_size
        self.music_sample_size = config.music_trans['downsample_rate']
        self.padding_size = config.music_trans['window_size'] // 2
    #     # logger.info("number of parameters: %e", sum(p.numel() for p in self.parameters()))
    def freeze_drop(self):
        for m in self.modules():
            if isinstance(m, nn.Dropout):
                m.eval()
                m.requires_grad = False
    # def get_block_size(self):
    #     return self.block_size

    # def _init_weights(self, module):
    #     if isinstance(module, (nn.Linear, nn.Embedding)):
    #         module.weight.data.normal_(mean=0.0, std=0.02)
    #         if isinstance(module, nn.Linear) and module.bias is not None:
    #             module.bias.data.zero_()
    #     elif isinstance(module, nn.LayerNorm):
    #         module.bias.data.zero_()
    #         module.weight.data.fill_(1.0)
    def get_block_size(self):
        return self.block_size
    
    def sample(self, xs, cond, shift=None, length=None, start_frame_index=0):
        
        block_size = self.get_block_size() - 1
        block_shift = block_size
        music_sample_rate = self.music_sample_size
        padding_size = self.padding_size

        x_up, x_down = xs
        assert x_up.size(1) >= shift, f"upper condition size less than initial shift, upper condition size: {x_up.size(1)}"
        assert x_down.size(1) >= shift, f"lower condition size less than initial shift, lower condition size: {x_up.size(1)}"
        # chop to fit shift size
        x_up = x_up[:,:shift]
        x_down = x_down[:,:shift]

        music_length = cond.size(1) // music_sample_rate - padding_size * 2
        if length is None:
            length = music_length
        else:
            length = min(music_length, length)

        for k in range(shift - 1, length):
            start_index = max(0, k + 1 - block_size)
            end_index = min(x_up.size(1), k + 1)
            x_cond_upper = x_up[:,start_index:end_index]
            x_cond_lower = x_down[:,start_index:end_index]

            music_k = k + start_frame_index
            music_start_index = (music_k + 1 - block_shift) * music_sample_rate if music_k >= block_size else 0
            music_end_index = min(cond.size(1) - 1, (music_k + 1 + padding_size * 2) * music_sample_rate)
            cond_input = cond[:, music_start_index: music_end_index]

            logits, _ = self.forward((x_cond_upper, x_cond_lower), cond_input)
            logit_up, logit_down = logits
            logit_up = logit_up[:, -1, :]
            logit_down = logit_down[:, -1, :]

            probs_up = F.softmax(logit_up, dim=-1)
            probs_down = F.softmax(logit_down, dim=-1)

            _, ix_up = torch.topk(probs_up, k=1, dim=-1)
            _, ix_down = torch.topk(probs_down, k=1, dim=-1)

            # append to the sequence and continue
            x_up = torch.cat((x_up, ix_up), dim=1)
            x_down = torch.cat((x_down, ix_down), dim=1)

        return ([x_up], [x_down])

    def forward(self, idxs, cond, targets=None):
        idx_up, idx_down = idxs
        
        targets_up, targets_down = None, None
        if targets is not None:
            targets_up, targets_down = targets
        
        # print('L238', cond.size())
        cond = self.music_trans(cond)
        # print(cond.size())
        feat = self.gpt_base(idx_up, idx_down, cond)
        logits_up, logits_down, loss_up, loss_down, entropy_up, entropy_down = self.gpt_head(feat, targets)
        # logits_down, loss_down = self.down_half_gpt(feat, targets_down)
        
        if loss_up is not None and loss_down is not None:
            loss = loss_up + loss_down
        else:
            loss = None

        return (logits_up, logits_down), loss

    def critic(self, idxs, cond):
        idx_up, idx_down = idxs
        
        with torch.no_grad():
            self.music_trans.eval()
            cond = self.music_trans(cond)
            self.gpt_base.eval()
            state = self.gpt_base(idx_up, idx_down, cond)
            self.gpt_base.train()
        values_up, values_down, _, _, _, _ = self.critic_net(state)
        value = values_up + values_down # up + down
        return value # value: NxTx1

    def actor(self, idxs, cond, targets=None, reduction=False):
        idx_up, idx_down = idxs
        # print(idxs[0][0])
        # print(targets[0])
        
        targets_up, targets_down = None, None
        if targets is not None:
            targets_up, targets_down = targets

        with torch.no_grad():
            self.music_trans.eval()
            cond = self.music_trans(cond)
            self.gpt_base.eval()
            feat = self.gpt_base(idx_up, idx_down, cond)
            self.gpt_base.train()

        logits_up, logits_down, loss_up, loss_down, entropy_up, entropy_down = self.gpt_head(feat, targets)
        
        # logits_down, loss_down, entropy_down = self.down_half_gpt(feat, targets_down, reduction=False, requires_entropy=True)
        
        if loss_up is not None and loss_down is not None:
            loss = loss_up + loss_down
        else:
            loss = None

        return (logits_up, logits_down), loss, entropy_up + entropy_down


class CausalCrossConditionalSelfAttention(nn.Module):
    """
    A vanilla multi-head masked self-attention layer with a projection at the end.
    It is possible to use torch.nn.MultiheadAttention here but I am including an
    explicit implementation here to show that there is nothing too scary here.
    """

    def __init__(self, config):
        super().__init__()
        assert config.n_embd % config.n_head == 0
        # key, query, value projections for all heads
        self.key = nn.Linear(config.n_embd, config.n_embd)
        self.query = nn.Linear(config.n_embd, config.n_embd)
        self.value = nn.Linear(config.n_embd, config.n_embd)
        # regularization
        self.attn_drop = nn.Dropout(config.attn_pdrop)
        self.resid_drop = nn.Dropout(config.resid_pdrop)
        # output projection
        self.proj = nn.Linear(config.n_embd, config.n_embd)
        # causal mask to ensure that attention is only applied to the left in the input sequence
        self.register_buffer("mask", torch.tril(torch.ones(config.block_size, config.block_size))
                                     .view(1, 1, config.block_size, config.block_size))
        # self.mask = se
        self.n_head = config.n_head

    def forward(self, x, layer_past=None):
        B, T, C = x.size()  # T = 3*t (music up down)

        # calculate query, key, values for all heads in batch and move head forward to be the batch dim
        k = self.key(x).view(B, T, self.n_head, C // self.n_head).transpose(1, 2) # (B, nh, T, hs)
        q = self.query(x).view(B, T, self.n_head, C // self.n_head).transpose(1, 2) # (B, nh, T, hs)
        v = self.value(x).view(B, T, self.n_head, C // self.n_head).transpose(1, 2) # (B, nh, T, hs)
        t = T // 3
        # causal self-attention; Self-attend: (B, nh, T, hs) x (B, nh, hs, T) -> (B, nh, T, T)
        att = (q @ k.transpose(-2, -1)) * (1.0 / math.sqrt(k.size(-1)))
        att = att.masked_fill(self.mask[:,:,:t,:t].repeat(1, 1, 3, 3) == 0, float('-inf'))
        att = F.softmax(att, dim=-1)
        att = self.attn_drop(att)
        y = att @ v # (B, nh, T, T) x (B, nh, T, hs) -> (B, nh, T, hs)
        y = y.transpose(1, 2).contiguous().view(B, T, C) # re-assemble all head outputs side by side

        # output projection
        y = self.resid_drop(self.proj(y))
        return y

class Block(nn.Module):
    """ an unassuming Transformer block """

    def __init__(self, config):
        super().__init__()
        self.ln1 = nn.LayerNorm(config.n_embd)
        self.ln2 = nn.LayerNorm(config.n_embd)
        self.attn = CausalCrossConditionalSelfAttention(config)
        self.mlp = nn.Sequential(
            nn.Linear(config.n_embd, 4 * config.n_embd),
            nn.GELU(),
            nn.Linear(4 * config.n_embd, config.n_embd),
            nn.Dropout(config.resid_pdrop),
        )

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.mlp(self.ln2(x))
        return x

class CrossCondGPTBase(nn.Module):
    """  the full GPT language model, with a context size of block_size """

    def __init__(self, config):
        super().__init__()
        config = EasyDict(config)
        self.tok_emb_up = nn.Embedding(config.vocab_size_up, config.n_embd  )
        self.tok_emb_down = nn.Embedding(config.vocab_size_down, config.n_embd)
        self.pos_emb = nn.Parameter(torch.zeros(1, config.block_size*3, config.n_embd))
        self.cond_emb = nn.Linear(config.n_music, config.n_embd)
        self.drop = nn.Dropout(config.embd_pdrop)
        # transformer
        self.blocks = nn.Sequential(*[Block(config) for _ in range(config.n_layer)])
        # decoder head
        # self.ln_f = nn.LayerNorm(config.n_embd)

        self.block_size = config.block_size


        self.apply(self._init_weights)


        # logger.info("number of parameters: %e", sum(p.numel() for p in self.parameters()))

    def get_block_size(self):
        return self.block_size

    def _init_weights(self, module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            # module.weight.data.uniform_(math.sqrt(6.0/sum(module.weight.size())))
            module.weight.data.normal_(mean=0.0, std=0.02)
            if isinstance(module, nn.Linear) and module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.LayerNorm):
            module.bias.data.zero_()
            module.weight.data.fill_(1.0)

    def configure_optimizers(self, train_config):
        """
        This long function is unfortunately doing something very simple and is being very defensive:
        We are separating out all parameters of the model into two buckets: those that will experience
        weight decay for regularization and those that won't (biases, and layernorm/embedding weights).
        We are then returning the PyTorch optimizer object.
        """

        # separate out all parameters to those that will and won't experience regularizing weight decay
        decay = set()
        no_decay = set()
        whitelist_weight_modules = (torch.nn.Linear, )
        blacklist_weight_modules = (torch.nn.LayerNorm, torch.nn.Embedding)
        for mn, m in self.named_modules():
            for pn, p in m.named_parameters():
                fpn = '%s.%s' % (mn, pn) if mn else pn # full param name

                if pn.endswith('bias'):
                    # all biases will not be decayed
                    no_decay.add(fpn)
                elif pn.endswith('weight') and isinstance(m, whitelist_weight_modules):
                    # weights of whitelist modules will be weight decayed
                    decay.add(fpn)
                elif pn.endswith('weight') and isinstance(m, blacklist_weight_modules):
                    # weights of blacklist modules will NOT be weight decayed
                    no_decay.add(fpn)

        # special case the position embedding parameter in the root GPT module as not decayed
        no_decay.add('pos_emb')

        # validate that we considered every parameter
        param_dict = {pn: p for pn, p in self.named_parameters()}
        inter_params = decay & no_decay
        union_params = decay | no_decay
        assert len(inter_params) == 0, "parameters %s made it into both decay/no_decay sets!" % (str(inter_params), )
        assert len(param_dict.keys() - union_params) == 0, "parameters %s were not separated into either decay/no_decay set!" \
                                                    % (str(param_dict.keys() - union_params), )

        # create the pytorch optimizer object
        optim_groups = [
            {"params": [param_dict[pn] for pn in sorted(list(decay))], "weight_decay": train_config.weight_decay},
            {"params": [param_dict[pn] for pn in sorted(list(no_decay))], "weight_decay": 0.0},
        ]
        optimizer = torch.optim.AdamW(optim_groups, lr=train_config.learning_rate, betas=train_config.betas)
        return optimizer

    def forward(self, idx_up, idx_down, cond):
        b, t = idx_up.size()
        assert t <= self.block_size, "Cannot forward, model block size is exhausted."
        b, t = idx_down.size()
        assert t <= self.block_size, "Cannot forward, model block size is exhausted."

        # forward the GPT model
        # if self.requires_head:
        token_embeddings_up = self.tok_emb_up(idx_up) # each index maps to a (learnable) vector
        token_embeddings_down = self.tok_emb_down(idx_down) # each index maps to a (learnable) vector
        token_embeddings = torch.cat([self.cond_emb(cond), token_embeddings_up, token_embeddings_down ], dim=1)

        position_embeddings = torch.cat([self.pos_emb[:, :t, :], self.pos_emb[:, self.block_size:self.block_size+t, :], self.pos_emb[:, self.block_size*2:self.block_size*2+t, :]], dim=1) # each position maps to a (learnable) vector
        
        x = self.drop(token_embeddings + position_embeddings)

        x = self.blocks(x)
        # x = self.ln_f(x)

        return x
    def freeze_drop(self):
        for m in self.modules():
            if isinstance(m, nn.Dropout):
                m.eval()
                m.requires_grad = False
class CrossCondGPTHead(nn.Module):
    """  the full GPT language model, with a context size of block_size """

    def __init__(self, config):
        super().__init__()
        config = EasyDict(config)

        self.blocks = nn.Sequential(*[Block(config) for _ in range(config.n_layer)])
        # decoder head
        self.ln_f = nn.LayerNorm(config.n_embd)

        self.block_size = config.block_size
        self.head_up = nn.Linear(config.n_embd, config.vocab_size_up, bias=False)
        self.head_down = nn.Linear(config.n_embd, config.vocab_size_down, bias=False)

        self.apply(self._init_weights)

    def get_block_size(self):
        return self.block_size

    def _init_weights(self, module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            module.weight.data.normal_(mean=0.0, std=0.02)
            if isinstance(module, nn.Linear) and module.bias is not None:
                module.bias.data.zero_()
        elif isinstance(module, nn.LayerNorm):
            module.bias.data.zero_()
            module.weight.data.fill_(1.0)

    def configure_optimizers(self, train_config):
        """
        This long function is unfortunately doing something very simple and is being very defensive:
        We are separating out all parameters of the model into two buckets: those that will experience
        weight decay for regularization and those that won't (biases, and layernorm/embedding weights).
        We are then returning the PyTorch optimizer object.
        """

        # separate out all parameters to those that will and won't experience regularizing weight decay
        decay = set()
        no_decay = set()
        whitelist_weight_modules = (torch.nn.Linear, )
        blacklist_weight_modules = (torch.nn.LayerNorm, torch.nn.Embedding)
        for mn, m in self.named_modules():
            for pn, p in m.named_parameters():
                fpn = '%s.%s' % (mn, pn) if mn else pn # full param name

                if pn.endswith('bias'):
                    # all biases will not be decayed
                    no_decay.add(fpn)
                elif pn.endswith('weight') and isinstance(m, whitelist_weight_modules):
                    # weights of whitelist modules will be weight decayed
                    decay.add(fpn)
                elif pn.endswith('weight') and isinstance(m, blacklist_weight_modules):
                    # weights of blacklist modules will NOT be weight decayed
                    no_decay.add(fpn)

        # special case the position embedding parameter in the root GPT module as not decayed
        no_decay.add('pos_emb')

        # validate that we considered every parameter
        param_dict = {pn: p for pn, p in self.named_parameters()}
        inter_params = decay & no_decay
        union_params = decay | no_decay
        assert len(inter_params) == 0, "parameters %s made it into both decay/no_decay sets!" % (str(inter_params), )
        assert len(param_dict.keys() - union_params) == 0, "parameters %s were not separated into either decay/no_decay set!" \
                                                    % (str(param_dict.keys() - union_params), )

        # create the pytorch optimizer object
        optim_groups = [
            {"params": [param_dict[pn] for pn in sorted(list(decay))], "weight_decay": train_config.weight_decay},
            {"params": [param_dict[pn] for pn in sorted(list(no_decay))], "weight_decay": 0.0},
        ]
        optimizer = torch.optim.AdamW(optim_groups, lr=train_config.learning_rate, betas=train_config.betas)
        return optimizer

    def forward(self, x, targets=None):

        x = self.blocks(x)
        x = self.ln_f(x)
        N, T, C = x.size()
        t = T//3
        logits_up = self.head_up(x[:, t:t*2, :])
        logits_down = self.head_down(x[:, t*2:t*3, :]) # down half 

        # if we are given some desired targets also calculate the loss
        loss_up, loss_down = None, None

        if targets is not None:
            targets_up, targets_down = targets

            loss_up = F.cross_entropy(logits_up.view(-1, logits_up.size(-1)), targets_up.view(-1), reduction='none')
            loss_down = F.cross_entropy(logits_down.view(-1, logits_down.size(-1)), targets_down.view(-1), reduction='none')
            
            
        logits_up_flat = logits_up.view(-1, logits_up.size(-1)) # NT * C
        entropy_up = - (F.softmax(logits_up_flat, dim=-1) * F.log_softmax(logits_up_flat, dim=-1)).sum(dim=-1)
        
        logits_down_flat = logits_down.view(-1, logits_down.size(-1)) # NT * C
        entropy_down = - (F.softmax(logits_down_flat, dim=-1) * F.log_softmax(logits_down_flat, dim=-1)).sum(dim=-1)

                
        return logits_up, logits_down, loss_up, loss_down, entropy_up, entropy_down

    def freeze_drop(self):
        for m in self.modules():
            if isinstance(m, nn.Dropout):
                m.eval()
                m.requires_grad = False

