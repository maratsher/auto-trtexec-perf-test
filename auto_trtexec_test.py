from sys import argv
import argparse
import os
import re

def cartesianProduct(set_a, set_b):
    result =[]
    for i in range(0, len(set_a)):
        for j in range(0, len(set_b)):
 
            if type(set_a[i]) != list:        
                set_a[i] = [set_a[i]]
            temp = [num for num in set_a[i]]  
            temp.append(set_b[j])            
            result.append(temp) 
             
    return result
 
# находим декартова произведение N множеств
def Cartesian(list_a, n):

    temp = list_a[0]
     
    for i in range(1, n):
        temp = cartesianProduct(temp, list_a[i])
         
    return temp

# создаем list из файла
def make_list(file):
    lst = []
    with open(file) as file:
        lines = file.readlines()
        reg = r"\[(.*?)\]"
        regp = r"\{(.*?)\}"
        print("ЗАШЛИ В ФАЙЛ")
        for l in lines:
            l = l.strip()
            m = re.findall(reg, l)
            mp = re.findall(regp, l)
            if(len(m) > 1):
                print("Input structure data error.")
                exit()
            elif len(m) == 0:
                if l == "NULL":
                    lst.append("")
                else:
                    lst.append(l)
            elif len(m) == 1:
                l = l.split(' ')[0]
                for v in m[0].split(" "):
                    if(len(mp) == 1):
                        lst.append(l+"="+os.path.join(mp[0], v))
                    else:
                        lst.append(l+"="+v)
    print(lst)
    return lst
 
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sd', type=str, default='./', help='Save dir')
    parser.add_argument('--pd', type=str, default='./params', help='Dir with params for models')
    parser.add_argument('--gp', type=str, default='./global-params.txt', help='File with global params')
    parser.add_argument('--te', type=str, default='./', help='Trtexec bin dir')
    parser.add_argument('--qps', type=int, default=-1, help='qps condition')
    parser.add_argument('--dev', type=bool, default=False, help='Dev mode')

    opt = parser.parse_args()
    print(opt)

    if not os.path.isdir(opt.sd):
        print(opt.sd + " is not dir")
        exit()

    if not os.path.isdir(opt.pd):
        print(opt.pd + " is not dir")
        exit()
    
    if not os.path.exists(os.path.join(opt.te, "trtexec")):
        print("Could not find "+os.path.join(opt.te, "trtexec"))
        exit()

    if not os.path.exists(opt.gp):
        print("Global params file " +opt.gp+ " dont exist")
        exit()

    params_dir = opt.pd
    with open(opt.gp) as file:
        global_params = file.readline()
    
    # список списков параметров
    L = []

    # разворачиваем файлы с параметрами в списки
    for file in sorted(os.listdir(params_dir)):
        filename = os.fsdecode(file)
        if filename.endswith(".txt"):
            L.append(make_list(os.path.join(params_dir, filename)))
            continue
        else:
            continue

    # запускаем trtexec для каждого набора параметров
    np = len(L) # кол-во параметров
    sets = Cartesian(L,np)
    nm = len(sets) # кол-во моделей
    print(f"ВСЕГО МОДЕЛЕЙ: {nm}")
    print("\n\n\n\n")
    for i, set in enumerate(Cartesian(L,np)):
        params = ""
        params = " ".join(set)

        # формируем имя для сохроняемого файла name.txt
        name = re.sub(r'\W+', '_', params)
        # скращаем имя
        name = name[name.find("weights"):]
        # нумеруем
        #name = str(i+1)+"_"+name

        # формируем строку исполняемой комманды
        command = str(opt.te) + "./trtexec "+ params + " "+global_params + " > buff.txt"
        command = " ".join(command.split()) 
        print(command)
        
        if not opt.dev:
            # если в save_dir уже есть файл с таким именем, пропускаем
            if os.path.exists(os.path.join(opt.save_dir, name+".txt")):
                print(os.path.join(opt.save_dir, name+".txt") + " уже сущесвует! Модель пропущена...")
                continue
            # выполянем команду
            try:
                os.system(command) 
                pass
            except Exception as e:
                print("Команда {command} выполнена с ошибкой {e}")
                continue
            #os.system("python3 emulator.py > buff.txt")

            # ищем в выводе trtexec qps
            key_word = 'Throughput'
            qps = 0
            with open('buff.txt', 'r') as fp:
                lines = fp.readlines()
                for line in lines:
                    if line.find(key_word) != -1:
                        qps = float(line.split(" ")[3])
                        break
            
            print(f"QPS: {qps}")

            if (opt.qps == -1):
                os.rename("buff.txt", os.path.join(opt.save_dir, name+".txt"))
            # сранвивам qps, если вышли за рамки, завершаем программу
            elif(qps < 10): # <
                print(f"Модель {name} вышла за рамки. Throughput {qps} qps" )
                print("Тестирование завершено!")
                exit()
            else:
                # если все хорошо, перемещаем буффер и save-dir с именем name.txt
                os.rename("buff.txt", os.path.join(opt.save_dir, name+".txt"))

            print()
            print("="*100)
            print(f"Протестированно {i+1} из {nm} моделей")
            print("="*100)
            print()
        

print("Тестирование завершено!")