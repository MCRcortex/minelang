def find_block(data,ending='}'):
    start=False
    index_counter=0
    for index,line in enumerate(data):
        if line=="{":
            start=True
            index_counter+=1
        if line=="}":
            index_counter-=1
        if start and index_counter==0 and line==ending:
            return index






class Scope:
    def __init__(self,parent,top=False):
        self.variable_scope={}
        self.function_scope=[]#{}        
        self.childern=[]
        if not top:
            parent.childern.append(self)
            self.parent=parent
        self.top=top
    def get_vars_in_scope(self):
        Vars=list(self.variable_scope.keys())
        if not self.top:
            Vars.extend(self.parent.get_variable_vars_in_scope())
        return Vars
    def get_funcs_in_scope(self):
        funcs=self.function_scope.copy()
        if not self.top:
            funcs.extend(self.parent.get_funcs_in_scope())
        return funcs
    def __repr__(self):
        return str(self.childern)+" : "+str(self.variable_scope)+" | "+str(self.function_scope)


class If:
    def __init__(self,info,internal_data,parent_scope):
        internal_data=internal_data[1:-1]
        self.condition=Expression(")".join("(".join(info.split("(")[1:]).split(")")[:-1]),parent_scope)
        self.parent_scope=parent_scope
        self.code=process_code(internal_data,Scope(scope))
    def __repr__(self):
        return "if "+str(self.condition)+" then {"+str(self.code)+"}"

    def compile(self):
        pass


class Expression:
    def __init__(self,expresion,scope):
        self.scope=scope
        self.code=expresion
    def __repr__(self):
        return str(self.code)
    
    def compile(self):
        pass

    
class function:
    def __init__(self,return_type,name,params,internal_data,parent_scope):
        declearFunction(name,parent_scope)
        
        self.parent_scope=parent_scope
        self.return_type =return_type
        self.name=name
        self.params=params
        self.code=process_code(internal_data,Scope(parent_scope))
  
    def __repr__(self):
        return str(self.code)

    def compile(self):
        pass


class SetVar:
    def __init__(self,variable_name,expresion,scope):
        self.variable_name=variable_name
        self.expresion=Expression(expresion,scope)
        self.scope=scope
    def __repr__(self):
        return self.variable_name + " = " + str(self.expresion)

    def compile(self):
        pass

class call_function:
    def __init__(self,what_function,args,scope):
        self.scope=scope
        self.function=what_function
        self.args=args
    def __repr__(self):
        return self.function+"("+str(self.args)+")"

    def compile(self):
        pass

    
class raw:
    def __init__(self,_,data,scope):
        self.data=data[1:-1]
        self.scope=scope
    def __repr__(self):
        return str(self.data)

    def compile(self):
        pass


    
def declearInt(info,scope):
    info=info.replace("="," = ").rstrip(";")
    while "  " in info:
        info=info.replace("  "," ")
    info=info.split(' ')
    name=info[1]
    value=info[3]
    scope.variable_scope[name]=value

def declearFunction(name,scope):
    scope.function_scope.append(name)

    
blockFunctions={"if":If,"raw":raw}
var_delerations={"int":declearInt}



def process_code(data,scope):
    index=0
    code=[]
    while index!=len(data):
        did_block=False
        for name in blockFunctions:
            if data[index].startswith(name):
                block=find_block(data[index+1:],"}")#";")
                block_data=data[index:block+index+2]
                code.append(blockFunctions[name](block_data[0],block_data[1:],Scope(scope)))
                index+=block+2
                did_block=True
                break
        if did_block:
            continue
        if data[index].split(" ")[0] in var_delerations.keys():
            var_delerations[data[index].split(" ")[0]](data[index],scope)
            index+=1
            continue
        line=data[index]
        line=line.replace("="," = ").rstrip(";")
        while "  " in line:
            line=line.replace("  "," ")
        line_split=line.split(' ')
        if len(line_split)==3:
            if line_split[1]=="=":
                code.append(SetVar(line_split[0],' '.join(line_split[2:]),scope))
                index+=1
                continue
        
        line=line.replace("("," ( ")
        while "  " in line:
            line=line.replace("  "," ")
        line_split=line.split(" ")
        funcs=scope.get_funcs_in_scope()
        if line_split[0] in funcs:
            code.append(call_function(line_split[0],")".join("(".join(info.split("(")[1:]).split(")")[:-1]),scope))
        index+=1
    return code


function_starters=["void","int"]


data=[i.rstrip("\r").rstrip("\n").replace("\t","    ").rstrip(" ").lstrip(" ") for i in open("test.txt").read().replace(";",";\n").replace("{","\n{\n").replace("}","\n}\n").split("\n")]#need to remove tabs and double spaces
in_function=False
index_counter=0
funcData=[]
code=[]

scope=Scope(None,True)


for line in data:
    if line=="":
        continue
    if line.split(" ")[0] in function_starters:
        in_function=True
    if in_function:
        funcData.append(line)
    for char in line:
        if char=="{":
            index_counter+=1
        if char=="}":
            index_counter-=1
        if char==";" and index_counter==0:
            info=funcData[0]
            funcData=funcData[2:-2]

            return_type=info.split(" ")[0]
            name=info.split(" ")[1].split("(")[0].rstrip(" ")
            
            parameters=[i.rstrip(" ").lstrip(" ") for i in info.split("(")[1].split(")")[0].split(",")]
            
            code.append(function(return_type,name,parameters,funcData,scope))
            funcData=[]
            in_function=False

print(code)
