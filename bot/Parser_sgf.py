import re
from typing import List, Dict, Any, Optional

class SGFNode:
    def __init__(self, properties: Dict[str, List[str]] = None):
        self.properties = properties or {}
        self.children: List[SGFNode] = []
    
    def get_property(self, key: str) -> Optional[str]:
        return self.properties.get(key, [None])[0]
    
    def __str__(self) -> str:
        props = ';'.join(f"{k}[{v[0]}]" for k, v in self.properties.items() if v)
        children = ''.join(str(child) for child in self.children)
        return f"(;{props}{children})"

class SGFParser:
    def __init__(self):
        self.nodes: List[SGFNode] = []
    
    def parse(self, sgf_string: str) -> List[SGFNode]:
        sgf_string = re.sub(r'\s+', '', sgf_string)
        
        node_pattern = r'\((;([^;)]*?)(.*?)\)'
        
        def parse_recursive(match):
            props_str, children_str = match.groups()
            node = self._parse_properties(props_str)
            
            child_matches = re.findall(node_pattern, children_str)
            for child_match in child_matches:
                child_node = parse_recursive(child_match)
                node.children.append(child_node)
            
            return node
        

        root_matches = re.findall(node_pattern, sgf_string)
        self.nodes = [parse_recursive(match) for match in root_matches]
        return self.nodes
    
    def _parse_properties(self, props_str: str) -> SGFNode:

        node = SGFNode()
        prop_pattern = r'([A-Z]+)\[(.*?)(?=\]|$)\]'
        props = re.findall(prop_pattern, props_str)
        
        for key, value in props:
            value = self._decode_sgf_value(value)
            if key not in node.properties:
                node.properties[key] = []
            node.properties[key].append(value)
        
        return node
    
    #парс в массив в gtp формате 
    def get_all_moves(self, root_node: SGFNode = None) -> List[List[str]]:

        if root_node is None:
            root_node = self.nodes[0] if self.nodes else None
        
        if not root_node:
            return []
        
        moves = []
        current_node = root_node
        
        while current_node:
            move = self._extract_move(current_node)
            if move:
                moves.append(move)
            
            if current_node.children:
                current_node = current_node.children[0]
            else:
                break
        
        return moves

    def _extract_move(self, node: SGFNode) -> List[str] | None:
       
       
        b_move = node.get_property('B')
        if b_move:
            return ['B', b_move]
        
        
        w_move = node.get_property('W')
        if w_move:
            return ['W', w_move]
        
        return None 

    def _decode_sgf_value(self, value: str) -> str:
        
        value = re.sub(r'\\\\', '\\', value)
        value = re.sub(r'\\]', ']', value)
        return value
        



def main():
    sgf_content = """
    (;GM[1]FF[4]SZ[19]KM[6.5]PB[Black]PW[White]
    ;B[pq]  
    ;W[dn] 
    ;B[fq]
    ;W[dq]
    (;B[pd];W[od]) 
    (;B[pc];W[oc])) 
    """
    
    parser = SGFParser()
    nodes = parser.parse(sgf_content)
    root = nodes[0]
    
    moves = parser.get_all_moves(root)
    

