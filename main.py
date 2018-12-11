
def is_num(test):
    try:
        int(test)
        return True
    except:
        return False
def find_block(data,ending='}',inc="{",dec="}"):
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

functions_code={}
def addSeperetCode(name,code,Compile=True):
    if Compile:
        functions_code[name]=code.compile()
        return
    functions_code[name]=code



pre_start=["/scoreboard objectives remove constants","/scoreboard objectives add constants dummy",
           "/scoreboard objectives remove variables","/scoreboard objectives add variables dummy",
           "/scoreboard objectives remove return_vals","/scoreboard objectives add return_vals dummy",
           "/scoreboard objectives remove temp","/scoreboard objectives add temp dummy",]
consts=[]
def add_constant(name,value):
    name=str(name)
    value=str(value)
    if not name in consts:
        pre_start.append("/scoreboard players set "+name+" constants "+value)
        consts.append(name)

temp_counter=0
    
class Scope:
    def __init__(self,parent,top=False):
        if top:
            self.id=0
        else:
            self.id=parent.id+1
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
    def get_all_child_vars_in_scope(self):
        Vars=self.variable_scope.copy()
        for i in self.childern:
            vars_remote=i.get_all_child_vars_in_scope()
            for val in vars_remote:
                Vars[i.get_var_name_in_scope(val)]=vars_remote[val]
        return Vars
    def __repr__(self):
        return str(self.childern)+" : "+str(self.variable_scope)+" | "+str(self.function_scope)
    def get_var_name_in_scope(self,name):
        if not name in  self.variable_scope.keys():
            if self.top:
                print("ERROR",name,"DOESNT EXIST")
            return self.parent.get_var_name_in_scope(name)
        return str(self.id)+"_"+name
    def get_func_name_in_scope(self,name):
        return name

ifCounter=0
class If:
    def __init__(self,info,internal_data,parent_scope):
        global ifCounter
        self.id=ifCounter
        ifCounter+=1
        internal_data=internal_data[1:-1]
        self.condition=Expression(")".join("(".join(info.split("(")[1:]).split(")")[:-1]),parent_scope)
        self.parent_scope=parent_scope
        self.local_scope=Scope(scope)
        self.code=process_code(internal_data,self.local_scope)
    def __repr__(self):
        return "if "+str(self.condition)+" then {"+str(self.code)+"}"
    
    def compile(self):        
        name="if_"+str(self.id)
        addSeperetCode(name,[i.compile() for i in self.code],False)
        add_constant(1,1)
        code=self.condition.compile()
        code.append("/execute if score expression return_vals = 1 constants run function program:"+self.local_scope.get_func_name_in_scope(name))
        
        return code

import ast
bin_op_to_char={ast.Add:"+",
            ast.Sub:"-",
            ast.Mult:"*",
            ast.Div:"/",
            ast.Module:"%"}
com_op_to_char={ast.Eq:"=",#MAYBE MAKE SO THAT IT SUPPORTS 9<10<11
                ast.Gt:">",
                ast.Lt:"<",}
def process_equation(op):
    if type(op)==ast.BinOp:
        return [bin_op_to_char[type(op.op)],process_equation(op.left),process_equation(op.right)]
    if type(op)==ast.Compare:
        return [com_op_to_char[type(op.ops[0])],process_equation(op.left),process_equation(op.comparators[0])]
    if type(op)==ast.Num:
        return ["int",str(op.n)]
    if type(op)==ast.Name:
        return ["var",op.id]
    if type(op)==ast.Call:
        return ["fuc",op.func.id,[process_equation(i)for i in op.args]]
    return op
def build_expression(code,output,scope,left=False):#Code produced can be optimised
    if code[0][0] in list("+-/*%><="):
        a=build_expression(code[1],output,scope,True)
        b=build_expression(code[2],output,scope)
        if code[0] in "+-/*%":
            output.append("/scoreboard players operation "+a+" "+code[0]+"= "+b)
            return a
        else:
            output.append("/scoreboard players set temp_0 temp 0")
            output.append("/execute if score "+a+" "+code[0]+" "+b+" run scoreboard players set temp_0 temp 1")
            output.append("/scoreboard players operation "+a+" = temp_0 temp")
            return a
    global temp_counter
    if left:
        temp_counter+=1
        temp=str(temp_counter)
    if code[0]=="int":
        add_constant(code[1],code[1])
        if left:
            output.append("/scoreboard players operation "+temp+" temp = "+str(code[1])+" constants")
            return temp+" temp"
        return str(code[1])+" constants"
    if code[0]=="var":
        code[1]=scope.get_var_name_in_scope(code[1])
        if left:
            output.append("/scoreboard players operation "+temp+" temp = "+str(code[1])+" variables")
            return temp+" temp"
        return str(code[1])+" variables"
    if code[0]=="fuc":
        print(code)
        output.append(call_function(code[1],code[2],scope,True).compile())
        if left:
            output.append("/scoreboard players operation "+temp+" temp = result return_vals")
            return temp+" temp"
        return "result return_vals"
class Expression:# returns the value in scoreboard     expression return_vals
    def __init__(self,expresion,scope):
        self.scope=scope
        self.code=expresion.replace("= =","==")
    def __repr__(self):
        return str(self.code)
    
    def compile(self):
        tree=process_equation(ast.parse(self.code).body[0].value)
        out=[]
        name=build_expression(tree,out,self.scope)
        out.append("/scoreboard players operation expression return_vals = "+name)
        return out




functions={}
class function:#if function returns a value it must be stored in scoreboard     result return_vals
    def __init__(self,return_type,name,params,internal_data,parent_scope):
        temp=[]
        for i in params:
            if not i=="":
                temp.append(i.lstrip("int "))#just for now assuming everything is an int
        params=temp
        declearFunction(name,parent_scope)
        self.parent_scope=parent_scope
        self.return_type =return_type
        self.name=name
        self.params=params
        self.current_scope=Scope(parent_scope)
        functions[name]=self
        for param in params:
            self.current_scope.variable_scope[param]='0'
        self.code=process_code(internal_data,self.current_scope)
      
    def __repr__(self):
        return str(self.code)

    def compile(self):
        return [code.compile() for code in self.code]


class SetVar:
    def __init__(self,variable_name,expresion,scope):
        self.variable_name=variable_name
        self.expresion=Expression(expresion,scope)
        self.scope=scope
    def __repr__(self):
        return self.variable_name + " = " + str(self.expresion)

    def compile(self):
        code=self.expresion.compile()
        code.append("/scoreboard players operation "+self.scope.get_var_name_in_scope(self.variable_name)+" variables = expression return_vals")
        return code

class call_function:
    def __init__(self,what_function,args,scope,from_expression=False):
        self.scope=scope
        self.function=what_function
        if from_expression:
            self.args=[i[1]for i in args]
        else:
            self.args=[i.lstrip(" ").rstrip(" ")for i in args.split(",")]
        
    def __repr__(self):
        return self.function+"("+str(self.args)+")"

    def compile(self):#NEED TO ADD, SETTING ARGS
        code=[]
        func=functions[self.function]
        for index,name in enumerate(self.args):
            if is_num(name):
                code.append("/scoreboard players set "+func.current_scope.get_var_name_in_scope(func.params[index])+" variables "+name)
            else:
                code.append("/scoreboard players operation "+func.current_scope.get_var_name_in_scope(func.params[index])+" variables = "+self.scope.get_var_name_in_scope(name)+" variables")
        code.append("/function program:"+scope.get_func_name_in_scope(func.name))
        print(code)
        return code

    
class raw:
    def __init__(self,_,data,scope):
        self.data=data[1:-1]
        self.scope=scope
    def __repr__(self):
        return str(self.data)

    def compile(self):
        return self.data


    
def declearInt(info,scope):#ADD EXPRESTION
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


#the main processing part of the code, goes through and maps out the process tree 
def process_code(data,scope):
    index=0
    code=[]
    while index!=len(data):
        
        #Processes block items such as functions,raw,if statments
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

        #process variable declerations
        if data[index].split(" ")[0] in var_delerations.keys():
            var_delerations[data[index].split(" ")[0]](data[index],scope)
            index+=1
            continue


        #process varible seting from expresion 
        line=data[index]
        line=line.replace("="," = ").rstrip(";")
        while "  " in line:
            line=line.replace("  "," ")
        line_split=line.split(' ')
        if len(line_split)>1:
            if line_split[1]=="=":
                code.append(SetVar(line_split[0],' '.join(line_split[2:]),scope))
                index+=1
                continue


        #process function calling
        line=line.replace("("," ( ")
        while "  " in line:
            line=line.replace("  "," ")
        line_split=line.split(" ")
        funcs=scope.get_funcs_in_scope()
        if line_split[0] in funcs:
            code.append(call_function(line_split[0],")".join("(".join(line.split("(")[1:]).split(")")[:-1]),scope))
        index+=1
    return code


function_starters=["void","int"]


Data=[i.rstrip("\r").rstrip("\n").replace("\t","    ").rstrip(" ").lstrip(" ") for i in open("test.txt").read().replace(";",";\n").replace("{","\n{\n").replace("}","\n}\n").split("\n")]#need to remove tabs and double spaces
in_function=False
index_counter=0
funcData=[]
code=[]

scope=Scope(None,True)


for line in Data:
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

for i in code:
    addSeperetCode(i.name,i)
pre_function_data=functions_code
function_data={}
def do_function_data(name,data):
    if type(data)==type([]):
        for i in data:
            do_function_data(name,i)
    else:
        function_data[name].append(data)
for func in pre_function_data:
    function_data[func]=[]
    do_function_data(func,pre_function_data[func])

start_function=[]

start_function.extend(pre_start)
Vars=scope.get_all_child_vars_in_scope()

for variable in Vars:
    start_function.append("/scoreboard players set "+variable+" variables "+Vars[variable])

function_data["prep_function"]=start_function


for function in function_data:
    f=open("code/data/program/functions/"+function+".mcfunction","w")
    f.write("\n".join([i[1:] for i in function_data[function]]))
    f.close()
