from typing import Optional

import torch
from torch import nn, Tensor
from einops import repeat
from transformers.modeling_outputs import BaseModelOutput

from utils.const import BlockType
from utils.AttnBlocksConf import AttnBlocksConf
from utils.DevConf import DevConf
from utils.AttnBlocks import AttnBlocks
from model.blocks.CALBlocks import CALBlocks
from model.blocks.CACBlocks import CACBlocks
from model.blocks.CAPBlocks import CAPBlocks


class SentiClassifier(nn.Module):
    def __init__(
            self,
            conf: AttnBlocksConf,
            blockType: str=BlockType.LAST,
            devConf: DevConf=DevConf()
        ):
        super(SentiClassifier, self).__init__()

        if conf.layerNum < 1:
            raise ValueError('layerNum must be greater than 0')
        elif conf.layerNum == 1:
            self.mapper = AttnBlocks(conf=conf, devConf=devConf)
        else:
            self.mapper = MapperFactory(conf=conf, blockType=blockType, devConf=devConf)
        self.IsNeedHiddenState = not (blockType == BlockType.LAST)
        self._Q = nn.Parameter(torch.randn(1, conf.hidDim, device=devConf.device, dtype=devConf.dtype))
        
        self._layerNum = conf.layerNum
    
    def forward(self,
            input: BaseModelOutput,
            returnAttnWeight: bool=False
        )->tuple[Tensor, Optional[Tensor]]:

        batch = input.last_hidden_state.size(0)
        sentVec, attnWeight = self.mapper.forward(repeat(self._Q, "l d -> b l d", b=batch), input, need_weights=True)
        
        if returnAttnWeight:
            return sentVec.squeeze(1), attnWeight
        return sentVec.squeeze(1)
    
def MapperFactory(
        conf: AttnBlocksConf,
        blockType: str=BlockType.LAST,
        devConf: DevConf=DevConf()
    )->nn.Module:
    if blockType == BlockType.LAST:
        return CALBlocks(conf, devConf)
    elif blockType == BlockType.CROSS:
        return CACBlocks(conf, devConf)
    elif blockType == BlockType.PARALLEL:
        return CAPBlocks(conf, devConf)
    else:
        raise ValueError('blockType must be either "last", "cross" or "parallel"')
    